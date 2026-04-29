# A Vibe coded FSI onboarding app

Before deploying this app, make sure you are on Domino 6.2.0 or higher, and the [Extended identity propogation](https://docs.dominodatalab.com/en/cloud/user_guide/cb9195/app-security-and-identity/#_extended_identity_propagation) feature is enabled

* Create a new project in your domino instance called `fsiapp`
* Copy the contents of the `fsi-onboarding-app` folder into your new project root
* Publish a new app from the project, using the `app.sh` file. Enable the "Deep Linking" and "Allow App to act for viewers" options when deploying
