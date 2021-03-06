import os

from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.generics import (CreateAPIView, ListAPIView,
                                     RetrieveAPIView, RetrieveUpdateAPIView,
                                     UpdateAPIView)
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from ...settings import EMAIL_HOST_USER
from .backends import Authentication
from .models import User
from .renderers import UserJSONRenderer
from .serializers import (LoginSerializer, RegistrationSerializer,
                          ResetSerializer, UserSerializer)
from .token import account_activation_token


class RegistrationAPIView(CreateAPIView):
    # Allow any user (authenticated or not) to hit this endpoint.
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = RegistrationSerializer

    def post(self, request):
        user = request.data.get('user', {})
        # The create serializer, validate serializer, save serializer pattern
        # below is common and you will see it a lot throughout this course and
        # your own work later on. Get familiar with it.
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user_details = User.objects.get(username=user['username'])

        subject = "VERIFY YOUR ACCOUNT"
        uid = urlsafe_base64_encode(force_bytes(user_details.id)).decode()
        token = account_activation_token.make_token(user)
        route = "{}".format(
            reverse('activate_account', kwargs={
                'pk': uid,
                'token': token
            })
        )
        activation_link = (
            "{scheme}://{host}{path}".format(
                scheme=request.scheme,
                host=request.get_host(),
                path=route,
            )
        )
        message = (
            "Hi {username},\n\n"
            "We are glad you have decided to join us. "
            "Please click the link below to activate you account.\n\n"
            "{activation_link}".format(
                username=user.get('username'),
                activation_link=activation_link,
            )
        )
        from_email = EMAIL_HOST_USER
        recipient = user.get('email')
        to_list = [recipient]
        send_mail(subject, message, from_email, to_list)
        user_data = serializer.data

        response_message = {
            "message": (
                "You have been registered successfully "
                "please check your email to activate your account"
            ),
            "user_data": user_data
        }

        return Response(response_message, status=status.HTTP_201_CREATED)


class LoginAPIView(CreateAPIView):
    renderer_classes = (UserJSONRenderer,)
    serializer_class = LoginSerializer

    def post(self, request):
        user = request.data.get('user', {})

        # Notice here that we do not call `serializer.save()` like we did for
        # the registration endpoint. This is because we don't actually have
        # anything to save. Instead, the `validate` method on our serializer
        # handles everything we need.

        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class UserRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = UserSerializer

    def retrieve(self, request, *args, **kwargs):
        # There is nothing to validate or save here. Instead, we just want the
        # serializer to handle turning our `User` object into something that
        # can be JSONified and sent to the client.
        serializer = self.serializer_class(request.user)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        serializer_data = request.data.get('user', {})

        # Here is that serialize, validate, save pattern we talked about
        # before.
        serializer = self.serializer_class(
            request.user, data=serializer_data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class RequestResetAPIView(CreateAPIView):
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = ResetSerializer

    def post(self, request):
        user_data = request.data['user']

        serializer = self.serializer_class(data=user_data)
        serializer.is_valid(raise_exception=True)

        # Pick the token from data
        token = serializer.data.get('token')

        # Format the email
        host = os.getenv('FRONTEND')
        resetpage = host + 'change_password/' + token
        subject = "Password Reset Request"
        message = (
            "Hello {user_data} you have requested for a password reset.\n"
            "If you wish to continue please press this link below\n\n{link}\n\n "
            "Else ignore this request.\n "
            "The link expires in 1 hour".format(user_data=user_data['email'], link=resetpage))
        from_email = EMAIL_HOST_USER
        to_list = [user_data['email']]

        # Send the email
        send_mail(
            subject,
            message,
            from_email,
            to_list, fail_silently=True
        )

        # Respond back to the user
        return Response(
            {"message": "Check your email for the link",
                "linker": resetpage},
            status=status.HTTP_200_OK)


class ResetPasswordAPIView(UpdateAPIView):
    renderer_classes = (UserJSONRenderer,)
    serializer_class = UserSerializer
    validation_checker = RegistrationSerializer

    def put(self, request, token, **kwargs):
        # Decode token
        decoded = Authentication.decode_jwt_token(token)

        # Validate the data
        self.validation_checker.validate_password(
            None,
            request.data['user']['password'])

        # Find the user instance with the the decoded username
        user = User.objects.get(username=decoded['username'])

        # Update the password
        self.serializer_class.update(
            None,
            user,
            {
                "password": request.data['user']['password']
            }
        )

        # Respond back to the user
        return Response(
            {"message": "Your password was successfully changed"},
            status=status.HTTP_200_OK)


class ActivateAccountAPIView(ListAPIView):
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = UserSerializer

    def get(self, request, **kwargs):

        try:
            uid64 = kwargs.get('pk')
            token = kwargs.get('token')
            uid = urlsafe_base64_decode(uid64).decode()
            account_details = User.objects.get(pk=uid)
        except (ValueError, TypeError, User.DoesNotExist):
            account_details = None
        finally:
            valid_token = default_token_generator.check_token(
                account_details, token=token
            )
            if account_details is not None and valid_token is not None:
                account_details.is_active = True
                account_details.save()
                return HttpResponseRedirect(
                    'https://authors-haven-ct-staging.herokuapp.com/', status.HTTP_201_CREATED
                )
        return HttpResponse('Invalid activation link')


class SocialAuthView(RetrieveAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request):
        """
        Social Authentication Frontend Redirect Endpoint

        This endpoint redirects the user to the frontend url responsible for setting user
        as authenticated.
        """

        if not request.user or not request.user.id:
            if '_auth_user_id' in request.session:
                user = User.objects.get(id=request.session['_auth_user_id'])

                return redirect("{}social/auth?success=true&username={}&new_user=false".format(
                    os.getenv("FRONTEND"),
                    user.username
                ))
            else:
                redirect("/api/auth/social/error")


class SocialAuthNewUserView(RetrieveAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request):
        """
        Social Authentication Frontend Redirect Endpoint

        This endpoint redirects the user to the frontend url responsible for setting user
        as authenticated.
        """

        if not request.user or not request.user.id:
            if '_auth_user_id' in request.session:
                user = User.objects.get(id=request.session['_auth_user_id'])

                return redirect("{}social/auth/social/auth?success=true&username={}&new_user=true".format(
                    os.getenv("FRONTEND"),
                    user.username
                ))

            else:
                redirect("/api/auth/social/error")


class SocialAuthErrorView(RetrieveAPIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        """
        Social Authentication Error Frontend Redirect Endpoint

        This endpoint redirects the user to the frontend to handle the output of the login error
        """

        return redirect("{}social/auth?success=false".format(
            os.getenv("FRONTEND")
        ))
