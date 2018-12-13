
from rest_framework import serializers


from .models import Profile


class GetProfileSerializer(serializers.ModelSerializer):
    """
    serializers for user profile upon user registration.
    """

    username = serializers.CharField(source='user.username')

    class Meta:
        model = Profile

        fields = ('username', 'bio', 'image', 'company', 'website', 'location', 'phone')
        read_only_fields = ("created_at", "updated_at")


class UpdateProfileSerializer(serializers.ModelSerializer):
    """
    serializers for user profile upon user registration.
    """

    class Meta:
        model = Profile

        fields = ('bio', 'image', 'company', 'website', 'location', 'phone')
        read_only_fields = ("created_at", "updated_at")

    def update(self, instance, validated_data):
        """
        Update profile function.
        """
        instance.bio = validated_data.get('bio', instance.bio)
        instance.image = validated_data.get('image', instance.image)
        instance.company = validated_data.get('company', instance.company)
        instance.website = validated_data.get('website', instance.website)
        instance.location = validated_data.get('location', instance.location)
        instance.phone = validated_data.get('phone', instance.phone)

        instance.save()
        return instance