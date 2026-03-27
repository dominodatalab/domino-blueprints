# A Vibe coded SCE Study publisher app

Before deploying this app, make sure you are on Domino 6.2.0 or higher, and the [Extended identity propogation](https://docs.dominodatalab.com/en/cloud/user_guide/cb9195/app-security-and-identity/#_extended_identity_propagation) feature is enabled

* Create a new project in your domino instance called `studyapp`
* Copy the contents of the `study-publisher` folder into your new project root
* Upload auth.json and codes.json to your new project's default dataset. Adjust the content as necessary to map your usernames
* Publish a new app from the project, using the `run.py` file. Enable the "Deep Linking" and "Allow App to act for viewers" options when deploying
