title: Gramex Authentication

## Sessions

Gramex identifies sessions through a secure cookie named `sid`, and stores
information against each session as a persistent key-value store. This is
available as `handler.session` in every handler. For example, here is the
contents of your [session](session) variable now:

<iframe frameborder="0" src="session"></iframe>

This has a `randkey` variable that was generated using the following code:

    :::python
    def store_value(handler):
        handler.session.setdefault('randkey', random.randint(0, 1000))
        return json.dumps(handler.session)

The first time a user visits the [session](session) page, it generates the
`randkey`. The next time this is preserved.

You can store any variable against a session. These are stored in the `sid`
secure cookie for a duration that's controlled by the `app.session.expiry`
configuration in `gramex.yaml`. Here is the default configuration:

    :::yaml
    app:
        session:
            expiry: 31                      # Session cookies expiry in days

The cookies are encrypted using the `app.settings.cookie_secret` key. Change
this to a random secret value, either via `gramex --settings.cookie_secret=...`
or in you `gramex.yaml`:

    :::yaml
    app:
        settings:
            cookie_secret: ...

# Authentication

Gramex allows users to log in using various single sign-on methods. The flow
is as follows:

1. Define a Gramex auth handler. This URL renders / redirects to a login page
2. When the user logs in, send the credentials to the auth handler
3. If credentials are valid, store the user details and redirect the user. Else
   show an error message.

## Google auth

This configuration creates a [Google login page](google):

    :::yaml
    url:
        login/google:
            pattern: /$YAMLURL/google   # Map this URL
            handler: GoogleAuth         # to the GoogleAuth handler
            kwargs:
                key: YOURKEY            # Set your app key
                secret: YOURSECRET      # Set your app secret

To get the application key and secret:

- Go to the [Google Dev Console](http://console.developers.google.com)
- Select a project, or create a new one.
- Enable the Google+ API service
- Under Credentials, create credentials for an OAuth client ID for a Web application
- Set the Authorized redirect URIs to point to your auth handler. (You can ignore Authorized Javascript origins)
- Copy the "Client secret" and "Client ID" to the application settings


## Facebook auth

This configuration creates a [Facebook login page](facebook):

    :::yaml
    url:
        login/facebook:
            pattern: /$YAMLURL/facebook # Map this URL
            handler: FacebookAuth       # to the FacebookAuth handler
            kwargs:
                key: YOURKEY            # Set your app key
                secret: YOURSECRET      # Set your app secret

- Go to the [Facebook apps page](https://developers.facebook.com/apps/)
- Select an existing app, or add a new app. Select website. You can skip the quick start.
- In the Settings tab on the left, set the URL of of your server's home page
- Copy the Application ID and App secret to the application settings


## Twitter auth

This configuration creates a [Twitter login page](twitter):

    :::yaml
    url:
        login/twitter:
            pattern: /$YAMLURL/twitter  # Map this URL
            handler: TwitterAuth        # to the TwitterAuth handler
            kwargs:
                key: YOURKEY            # Set your app key
                secret: YOURSECRET      # Set your app secret

- Go to the [Twitter home page](https://apps.twitter.com/)
- Select Create New App
- Enter a Name, Description and Website
- In the Callback URL, enter the URL of the auth handler
- Go to the Keys section of the app
- Copy the Consumer Key (API Key) and Consumer Secret (API Secret) to the application settings


## LDAP auth

This configuration creates an [LDAP login page](ldap):

    :::yaml
    auth/ldap:
        pattern: /$YAMLURL/ldap                 # Map this URL
        handler: LDAPAuth                       # to the LDAP auth handler
        kwargs:
            template: $YAMLPATH/ldap.html       # Render the login form template
            host: ipa.demo1.freeipa.org         # Server to connect to
            use_ssl: true                       # Whether to use SSL or not
            port: 636                           # Optional. Usually 389 for LDAP, 636 for LDAPS
            user: 'uid={user},cn=users,cn=accounts,dc=demo1,dc=freeipa,dc=org'
            password: '{password}'

The [login page](ldap) should provide a username, password and an [xsrf][xsrf]
field. Additional fields (e.g. for domain) are optional. The `user:` and
`password:` fields map these to the LDAP user ID and password. Strings inside
`{braces}` are replaced by form fields -- so if the user enters `admin` in the
`user` field, `uid={user},cn=...` becomes `uid=admin,cn=...`.

Here is a minimal `ldap.html` template:

    :::html
    <form method="POST">
      {% if error %}<p>error code: {{ error['code'] }}, message: {{ error['message'] }}</p>{% end %}
      <input type="hidden" name="_xsrf" value="{{ handler.xsrf_token }}">
      <input name="user">
      <input name="password" type="password">
      <button type="submit">Submit</button>
    </form>

[xsrf]: http://www.tornadoweb.org/en/stable/guide/security.html#cross-site-request-forgery-protection


## Database auth

This configuration lets you log in from a [database table](db):

    :::yaml
    pattern: /$YAMLURL/db                 # Map this URL
    handler: DBAuth                       # to the DBAuth handler
    kwargs:
        template: $YAMLPATH/dbauth.html     # Render the login form template
        url: sqlite:///$YAMLPATH/auth.db    # Pick up list of users from this sqlalchemy URL
        table: users                        # ... and this table
        user:
            column: user                  # The users.user column is matched with
            arg: user                     # ... the ?user= argument from the form
        password:
            column: password              # The users.password column is matched with
            arg: password                 # ... the ?password= argument from the form
            # If the database holds encrypted passwords, specify the same
            # encryption method here. If the form password is the same as the
            # database password, skip this section.
            function: passlib.hash.sha256_crypt.encrypt
            args: '=content'
            kwargs: {salt: 'secret-key'}

The [login page](db) should provide a username, password and an [xsrf][xsrf]
field. In this configuration, the usernames and passwords are stored in the `users`
table of the SQLite `auth.db` file. The `user` and `password` columns of the
table map to the `user` and `password` query arguments.

Here is a minimal `dbauth.html` template:

    :::html
    <form method="POST">
      {% if error %}<p>error code: {{ error['code'] }}, message: {{ error['message'] }}</p>{% end %}
      <input type="hidden" name="_xsrf" value="{{ handler.xsrf_token }}">
      <input name="user">
      <input name="password" type="password">
      <button type="submit">Submit</button>
    </form>

The password supports optional encryption. Before the password is compared with
the database, it is encrypted using the provided function. You can also use
client-side (JavaScript) instead, and disable this.

For an example of how to create users in a database, see `create_user_database`
from [authutil.py](authutil.py).


## Log out

This configuration creates a [logout page](logout):

    :::yaml
    auth/logout
        pattern: /$YAMLURL/logout   # Map this URL
        handler: LogoutHandler      # to the logout handler
        redirect:                   # Redirect options are applied in order
            query: next             # If ?next= is specified, use it
            url: /$YAMLURL          # Else redirect to the directory where this gramex.yaml is present

After logging out, the user is re-directed to the URL specified by `?next=`.
Else, they're redirected to the current page. Read the
[redirection](#redirection) section for more.

## Redirection after login

After users logs in, they are redirected based on the common `redirect:` section
in the auth handler kwargs. This redirect URL can be based on:

- a URL `query` parameter
- a HTTP `header`, or
- a direct `url`

For example:

    :::yaml
    url:
      login/google:
        pattern: /$YAMLURL/google
        handler: GoogleAuth
        kwargs:
          key: YOURKEY
          secret: YOURSECRET
          redirect:                 # Redirect options are applied in order
            query: next             # If ?next= is specified, use it
            header: Referer         # Else use the HTTP header Referer if it exists
            url: /$YAMLURL          # Else redirect to the directory where this gramex.yaml is present

If none of these is specified, the user is redirected to the home page `/`.

In the above configuration, [google?next=../config/](google?next=../config/)
will take you to the [config](../config/) page after logging in.

By default, the URL must redirect to the same server (for security reasons). So
[google?next=https://gramener.com/](google?next=https://gramener.com/) will
ignore the `next=` parameter. However, you can specify `external: true` to
override this:

    ::yaml
        kwargs:
          external: true

You can test this at
[ldap2?next=https://gramener.com/](ldap2?next=https://gramener.com/).

## Login actions

When a user logs in or logs out, you can register actions as follows:

    :::yaml
    url:
      login/google:
        pattern: /$YAMLURL/google
        handler: GoogleAuth
        kwargs:
          key: YOURKEY
          secret: YOURSECRET
          action:                                     # Run multiple function on Google auth
              -                                       # The first action
                function: ensure_single_session       #   ... logs user out of all other sessions
              -                                       # The section action
                function: sys.stderr.write            #   ... writes to the console
                args: 'Logged in via Google'          #   ... this message

For example, the [ldap login](ldap) page is set with `ensure_single_session`.
You can log in on multiple browsers. Every log in will log out other sessions.

You can write your own custom functions. By default, the function will be passed
the `handler` object. You can define any other `args` or `kwargs` to pass
instead. The actions will be executed in order.

When calling actions, `handler.current_user` will have the user object on all
auth handlers and the `LogoutHandler`.

## User attributes

All handlers store the information retrieved about the user in
`handler.session['user']`, typically as a dictionary. All handlers have access
to this information via `handler.current_user` by default.

## Logging logins

You can configure a logging action for when the user logs in or logs out via the
`log:` configuration. For example:

    auth/twitter:
        pattern: /$YAMLURL/twitter
        handler: TwitterAuth
        kwargs:
            key: XkCVNZD5sfWECxHGAGnlHGQFa
            secret: yU00bx5dHYMbge9IyO5H1KeC5uFnWndntG7u6CH6O4HDZHQg0p
            log:                                # Log this when a user logs in via this handler
                fields:                         # List of fields:
                  - session.id                  #   handler.session['id']
                  - current_user.username       #   handler.current_user['username']
                  - request.remote_ip           #   handler.request.remote_ip
                  - request.headers.User-Agent  #   handler.request.headers['User-Agent']

This will log the result into the `user` logger, which saves the data as a CSV file in `$GRAMEXDATA/logs/user.csv`. (See [predefined variables](../config/#predefined-variables) to locate `$GRAMEXDATA`.)

You can define your own logging handler for the `user` logger in the [log section](../config/#logging). Here's a sample definition:

    log:
        handlers:
            user:
                class: logging.handlers.FileHandler     # Save it as a file
                filename: $GRAMEXDATA/logs/user.csv     # under the Gramex data directory as logs/user.csv
                formatter: csv-message                  # Format message as-is. (Don't change this line)

You can also use more sophisticated loggers such as [TimedRotatingFileHandler](https://docs.python.org/3/library/logging.handlers.html#logging.handlers.TimedRotatingFileHandler).

# Authorization

To restrict pages to specific users, use the `kwargs.auth` configuration. This
works on all Gramex handlers (that derive from `BaseHandler`).

If you don't specify `auth:` in the `kwargs:` section, the `auth:` defined in
`app.settings` will be used. If that's not defined, then the handler is publicly
accessible to all.

`auth: true` just requires that you must log in. In this example, you can access
[must-login](must-login) only if you are logged in.

    url:
        auth/must-login:
            pattern: /$YAMLURL/must-login
            handler: FileHandler
            kwargs:
                path: $YAMLPATH/secret.html
                auth: true

`auth:` can also lets you define conditions. For example, you can access
[dotcom](dotcom) only if your email ends with `.com`, and access
[dotorg](dotorg) only if your email ends with `.org`.

    url:
        auth/dotcom:
            pattern: /$YAMLURL/dotcom
            handler: FileHandler
            kwargs:
                path: $YAMLPATH/secret.html
                auth:
                    condition:                          # Allow only if condition is true
                        function: six.string_type.endswith            # Call this function
                        args: [=handler.current_user.email, '.com']   # with these 2 arguments
        auth/dotorg:
            pattern: /$YAMLURL/dotorg
            handler: FileHandler
            kwargs:
                path: $YAMLPATH/secret.html
                auth:
                    condition:                          # Allow only if condition is true
                        function: six.string_type.endswith            # Call this function
                        args: [=handler.current_user.email, '.org']   # with these 2 arguments

You can specify any function of your choice. The function must return (or yield)
`True` to allow the user access, and `False` to raise a HTTP 403 error.

`auth:` can check for membership. For example, you can access [en-male](en-male)
only if your gender is `male` and your locale is `en` or `es`:

        auth:
            membership:           # The following user object keys must match
                gender: male      # user.gender must be male
                locale: [en, es]  # user.locale must be en or es

If the `user` object has nested attributes, you can access them via `.`. For
example, `attributes.cn` refers to `handlers.current_user.attributes.cn`.