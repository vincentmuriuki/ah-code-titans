$('.ui.form')
.form({
  fields: {
    username: {
      identifier: 'username',
      rules: [
        {
          type   : 'empty',
          prompt : 'Please enter a username'
        },
        {
            type   : 'regExp[/^[A-Za-z0-9_-]{4,}$/]',
            prompt : 'Please enter a username with at least 4 characters.'
        }
      ]
    },
    email: {
        identifier: 'email',
        rules: [
          {
            type   : 'empty',
            prompt : 'Please enter an email'
          },
          {
            type   : 'regExp[/^[a-zA-Z0-9\.]+@[a-zA-Z0-9\.]+\.[a-zA-Z]+$/]',
            prompt : 'Please enter a valid email'
        }
        ]
      },
    password: {
      identifier: 'password',
      rules: [
        {
          type   : 'empty',
          prompt : 'Please enter a password'
        },
        {
          type   : 'minLength[8]',
          prompt : 'Your password must be at least {ruleValue} characters'
        }
      ]
    },
    confirm_password: {
        identifier: 'confirm_password',
        rules: [
          {
            type   : 'empty',
            prompt : 'Please enter a confirm password'
          }
        ]
      }
  }
})
;