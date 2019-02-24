# Item Catalog Project

This project is intended to provide a tool to manage a number of items which belong to a series of categories. The developed application provides a registration and authentication system. As a result, only authenticated users obtain the authorization to add, edit or delete items. Furthermore, authenticated users will only be able to edit or delete those items they have created.

## Table of Contents

* [Description of the Project](#description-of-the-project)
* [Getting Started](#getting-started)
* [Contributing](#contributing)

## Description of the Project

The RESTful web application that implements the project's functionality uses the Python framework Flask. It interacts with a SQLite database, and provides third-party OAuth authentication. The application is best described by explaining its structure:

### Shared page header

There is a page header which is shown at all site pages. It allows the user to navigate to the homepage, and to log in and out of the system. In addition, once the user is authenticated, it shows its username and picture. The web banner image of the application is also shown throughout the site pages. Finally, any flashed messages can be shown just after the web banner image as part of the shared page header.

### Homepage

 The homepage provides a view of all categories in the system, and the latest added items. In addition, if a particular category is chosen, all of its items are shown. It is also possible to choose a particular item to navigate to a page where its information is displayed.

 Once the user has authenticated to the system, they are allowed to add a new item. Furthermore, choosing any item navigates the user to another page where they are able to see its information, and choose to either edit or delete it.

### Item creation page

An authenticated user is allowed to access this page from the homepage. Two options are possible. The first one allows the user to create a new item and indicate which category it will belong to. The second one is exactly the same but the category has already been selected by the user in the homepage. In any case, the user enters item title and description.

### Item information page

This page shows specific information about an item. If the user has already been authenticated to the system, it also allows them to link to the edit item or delete item pages, provided the user has created the item.

### Item edition page

This page allows an authenticated user to edit their own items. Both description and category can be edited.

### Item deletion page

This page allows an authenticated user to delete their own items. They are asked to confirm the deletion.

### JSON endpoints

The application provides six JSON API endpoints, where it is possible to obtain:

* The information of a category, e.g. http://localhost:8000/catalog/Snowboarding/category/JSON.
* The information of an item, e.g. http://localhost:8000/catalog/Frisbee/item/JSON.
* The information of all categories, e.g. http://localhost:8000/catalog/category/JSON.
* The information of all items, e.g. http://localhost:8000/catalog/item/JSON.
* The information of a category and its items, e.g. http://localhost:8000/catalog/Soccer/category/item/JSON.
* The information of the whole catalog. In other words, the information of all categories, and within each one, the information of all its items, e.g. http://localhost:8000/catalog/category/item/JSON.

## Getting Started

The main program built as part of this project, application.py, is run within a Linux-based virtual machine (VM). In order to run this program, you must:

* Install [VirtualBox](https://www.virtualbox.org/) and [Vagrant](https://www.vagrantup.com/).
* Configure the VM. To this end, fork and clone [this Github repository](https://github.com/udacity/fullstack-nanodegree-vm). Then, cd to the newly created directory, then to the vagrant directory, and finally to the catalog directory.
* Put these application's files into the catalog directory. The vagrant directory, and as a result the catalog directory, are outside your VM, but they are shared with it.
* Run `vagrant up` to start the virtual machine, and `vagrant ssh` to log in to it.
* Once logged into the VM, cd to the /vagrant directory, then to the catalog directory, and execute `python database_setup.py`. This command creates the application's database. Then execute `populatedb.py`. This command populates the application's database.
* That's it! You can now run the application.py file from the command line within the VM, in the /vagrant/catalog directory. As a result, you can access the application from [http://localhost:8000](http://localhost:8000)

This project is made up of a number of files. The main ones are:

* application.py: It contains the source code of the Python program that implements the main functionality of this Flask application.
* database_setup.py: It contains the commands that create the application's database.
* populatedb.py: It contains the commands that populate the application's database.
* client_secrets.json: It contains a number of OAuth2 parameters associated to the Google sign in for this application.
* static/styles.css: It contains the CSS to style the application.
* templates: This directory contains all HTML template files that provide the structure of the different pages of this web application.
* README.md: It contains the documentation file you are viewing right now.

## Contributing

This repository contains all the code that makes up the application. Individuals and I myself are encouraged to further improve this project. As a result, I will be more than happy to consider any pull requests.