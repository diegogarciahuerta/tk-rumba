![build](https://github.com/diegogarciahuerta/tk-rumba_pre/workflows/build/badge.svg)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

# Shotgun toolkit engine for Rumba

Contact : [Diego Garcia Huerta](https://www.linkedin.com/in/diegogh/)

![tk-rumba_04](config/images/tk-rumba_04.png)

## Overview

Implementation of a shotgun engine for [**Rumba**](https://rumba-animation.com/). It supports the classic bootstrap startup methodology and integrates with Rumba adding a new Shotgun Menu in the main Rumba tool-bar.

* [Engine Installation](#engine-installation)
* [Configuring your project for Shotgun Toolkit](#configuring-your-project-for-shotgun-toolkit)
* [Modifying the toolkit configuration files to add this engine and related apps](#modifying-the-toolkit-configuration-files-to-add-this-engine-and-related-apps)
* [Modifying the Templates](#modifying-the-templates)
* [Configuring Rumba in the software launcher](#configuring-rumba-in-the-software-launcher)
* [Caching and downloading the engine into disk](#caching-and-downloading-the-engine-into-disk)
* [Rumba engine should be ready to use](#rumba-engine-should-be-ready-to-use)
* [Toolkit Apps Included](#toolkit-apps-included)

With the engine, hooks for most of the standard tk applications are provided:

* [tk-multi-workfiles2](#tk-multi-workfiles2)
* [tk-multi-snapshot](#tk-multi-snapshot)
* [tk-multi-loader2](#tk-multi-loader2)
* [tk-multi-publish2](#tk-multi-publish2)
* [tk-multi-breakdown](#tk-multi-breakdown)
* [tk-multi-setframerange](#tk-multi-setframerange)

More:

* [Rumba engine options](#rumba-engine-options)
* [Development notes](#development-notes)
* [Rumba development notes](#rumba-development-notes)

**Disclaimer**

**This engine has been developed and tested in Windows 10 using Rumba version 1.0.1.**

The engine has not been used in production before so **use it at your own risk**. Also keep in mind that some of the hooks provided might need to be adapted to your work flows and pipelines. If you use it in production, I would love to hear about it, drop me a message in the contact link at the top of this documentation.

## Engine Installation

When I started using shotgun toolkit, I found quite challenging figuring out how to install and configure a new tk application or a new engine. Shotgun Software provides extensive documentation on how to do this, but I used to get lost in details, specially with so many configuration files to modify.

If you are familiar with how to setup an engine and apps, you might want to skip the rest of this document, just make sure to check the [templates](config/core/templates.yml) and [additions to the configs](config/env) that might give you a good start.
Also be sure to check  the options available for this engine here:

 [Rumba engine options](#rumba-engine-options)

If you are new to shotgun, I also recommend to read at least the following shotgun articles, so you get familiar with how the configuration files are setup, and the terminology used:

* [App and Engine Configuration Reference](https://support.shotgunsoftware.com/hc/en-us/articles/219039878-App-and-Engine-Configuration-Reference)
* [Overview of Toolkit's New Default Configuration](https://support.shotgunsoftware.com/hc/en-us/articles/115004077494-Overview-of-Toolkit-s-New-Default-Configuration-)

Here are detailed instructions on how to make this engine work assuming you use a standard shotgun toolkit installation and have downloaded shotgun desktop.

[Shotgun Desktop Download Instructions](https://support.shotgunsoftware.com/hc/en-us/articles/115000068574#Getting%20started%20with%20Shotgun%20Desktop)

Also an amazing resource to look for help when configuring your engine, is the [Shotgun Community Forums](https://community.shotgunsoftware.com/), specifically under *Pipeline Integrations* category.

Finally, this link contains the technical reference for Shotgun toolkit and related technologies, a great effort to collate all the tech documentation in a single place:

[Shotgun's Developer Documentation](https://developer.shotgunsoftware.com/)

## Configuring your project for Shotgun Toolkit

If you haven't done it yet, make sure you have gone through the basic steps to configure your project to use shotgun toolkit, this can be done in shotgun desktop app, by:

* enter into the project clicking it's icon

* click on the user icon to show more options (bottom right)

* click on *Advanced project setup*

    ![advanced_project_setup](config/images/advanced_project_setup.png)

* *Select a configuration*: "Shotgun Default" or pick an existing project that you have already setup pages and filters for.
![select_a_project_configuration](config/images/select_a_project_configuration.png)

* *Select a Shotgun Configuration*: select "default" which will download the standard templates from shotgun. (this documentation is written assuming you have this configuration)
![select_a_shotgun_configuration](config/images/select_a_shotgun_configuration.png)

* *Define Storages*: Make sure you name your first storage "primary", and a choose a primary folder where all the 'jobs' publishes will be stored, in this case "D:\demo\jobs" for illustrative purposes.
![define_storages](config/images/define_storages.png)

* *Project Folder Name*: This is the name of the project in disk. You might have some sort of naming convention for project that you might follow, or leave as it is. (My advice is that you do not include spaces in the name)
![project_folder_name](config/images/project_folder_name.png)

* *Select Deployment*: Choose "Centralized Setup". This will be the location of the configuration files (that we will be modifying later). For example, you could place the specific configuration for a project (in this example called game_config) within a folder called "configs" at the same level then the jobs folder, something like:

```shell
├───jobs
└───configs
    └───game_config
        ├───cache
        ├───config
        │   ├───core
        │   │   ├───hooks
        │   │   └───schema
        │   ├───env
        │   │   └───includes
        │   │       └───settings
        │   ├───hooks
        │   │   └───tk-multi-launchapp
        │   ├───icons
        │   └───tk-metadata
        └───install
            ├───apps
            ├───core
            ├───engines
            └───frameworks
```

(Note that this might not be suitable for more complex setups, like distributed configurations)
![select_deployment](config/images/select_deployment.png)

## Modifying the toolkit configuration files to add this engine and related apps

Every pipeline configuration has got different environments where you can configure apps accordingly. (for example you might want different apps depending if you are at an asset context or a shot context. The configured environments really depend on your projects requirements. While project, asset, asset_step, sequence, shot, shot_step, site are the standard ones, it is not uncommon to have a sequence_step environment or use a episode based environment either.

I've included a folder called 'config' in this repository where you can find the additions to each of the environments and configuration YAML files that come with the [default shotgun toolkit configuration repository](https://github.com/shotgunsoftware/tk-config-default2) (as of writing)

[configuration additions](config)

These YAML files provided **should be merged with the original ones as they won't work on their own.**

As an example, for the location of the engine, we use a git descriptor that allows up to track the code from a git repository. This allows easy updates, whenever a new version is released. So in the example above, you should modify the file:
``.../game_config/config/env/includes/engine_locations.yml``

and add the following changes from this file:
[engine_locations.yml](config/env/includes/engine_locations.yml)

```yaml
# Rumba
engines.tk-rumba.location:
  type: git
  branch: master
  path: https://github.com/diegogarciahuerta/tk-rumba.git
  version: v1.0.0
```

**Do not forget to update the version of the engine to the latest one. You can check here which one is the [latest version](https://github.com/diegogarciahuerta/tk-rumba/releases)**

In your environments you should add tk-rumba yml file, for example in the asset_step yml file:
``/configs/game_config/env/asset_step.yml``

Let's add the include at the beginning of the file, in the 'includes' section:

```yaml
- ./includes/settings/tk-rumba.yml
```

Now we add a new entry under the engines section, that will include all the information for our Rumba application:

```yaml
  tk-rumba: "@settings.tk-rumba.asset_step"
```

And so on.

Finally, do not forget to copy the additional `tk-rumba.yml` into your settings folder.

## Modifying the Templates

The additions to `config/core/templates.yml` are provided also under the config directory of this repository, specifically:

[templates.yml](config/core/templates.yml)

## Configuring Rumba in the software launcher

In order for our application to show up in the shotgun launcher, we need to add it to our list of software that is valid for this project.

* Navigate to your shotgun URL, ie. `example.shotgunstudio.com`, and once logged in, clink in the Shotgun Settings menu, the arrow at the top right of the web page, close to your user picture.
* Click in the Software menu
![select_a_project_configuration](config/images/select_a_project_configuration.png)

* We will create a new entry for Rumba, called "Rumba" and whose description can be conveniently copy and pasted from the [Rumba website](https://rumba-animation.com/)

![create_new_software](config/images/create_new_software.png)

* We now should specify the engine this software will use. "tk-rumba"

<img src="./config/images/software_specify_engine.png" width="50%" alt="software_specify_engine">

* Note that you can restrict this application to certain projects by specifying the project under the projects column. If no projects are specified this application will show up for all the projects that have this engine in their configuration files.

If you want more information on how to configure software launches, here is the detailed documentation from shotgun.

[Configuring software launches](https://support.shotgunsoftware.com/hc/en-us/articles/115000067493#Configuring%20the%20software%20in%20Shotgun%20Desktop)

## Caching and downloading the engine into disk

One last step is to cache the engine and apps from the configuration files into disk. Shotgun provides a tank command for this.

[Tank Advanced Commands](https://support.shotgunsoftware.com/hc/en-us/articles/219033178-Administering-Toolkit#Advanced%20tank%20commands)

* Open a console and navigate to your pipeline configuration folder, where you will find a `tank` or `tank.bat` file.
(in our case we placed the pipeline configuration under `D:\demo\configs\game_config`)

* type `tank cache_apps` , and press enter. Shotgun Toolkit will start revising the changes we have done to the configuration YAML files and downloading what is requires.

![tank_cache_apps](config/images/tank_cache_apps.png)

## Rumba engine should be ready to use

If we now go back and forth from our project in shotgun desktop ( < arrow top left if you are already within a project ), we should be able to see Rumba as an application to launch.

<img src="./config/images/engine_is_configured.png" width="50%" alt="engine_is_configured">

## Rumba engine options

`RUMBA_BIN_DIR`: defines where the rumba executable directory is. This is used in case you decide to install Rumba in a different location than the default. Note that the toolkit official way to achieve the same is by using [tk-multi-launchapp](https://github.com/shotgunsoftware/tk-multi-launchapp), but for less complicated cases, this environment variable should be sufficient.

`SGTK_RUMBA_CMD_EXTRA_ARGS`: defines extra arguments that will be passed to executable when is run. For example, you might want to run a script when Rumba starts up, this is an exmaple from the official documentation:

[Run a Python script using the command line](https://rumba-animation.com/doc/1.0/python/td.html?highlight=command%20line)

In this engine, panel support has been implemented, so for example the `Shotgun Panel` app can show as a floating window on its own, or docked anywhere in the Rumba user Interface.

## Toolkit Apps Included

## [tk-multi-workfiles2](https://support.shotgunsoftware.com/hc/en-us/articles/219033088)
![tk-rumba_07](config/images/tk-rumba_07.png)

This application forms the basis for file management in the Shotgun Pipeline Toolkit. It lets you jump around quickly between your various Shotgun entities and gets you started working quickly. No path needs to be specified as the application manages that behind the scenes. The application helps you manage your working files inside a Work Area and makes it easy to share your work with others.

Basic [hooks](hooks/tk-multi-workfiles2) have been implemented for this tk-app to work. open, save, save_as, reset, and current_path are the scene operations implemented.

Check the configurations included for more details:

[additions to the configs](config/env)

## [tk-multi-snapshot](https://support.shotgunsoftware.com/hc/en-us/articles/219033068)
![tk-rumba_08](config/images/tk-rumba_08.png)

A Shotgun Snapshot is a quick incremental backup that lets you version and manage increments of your work without sharing it with anyone else. Take a Snapshot, add a description and a thumbnail, and you create a point in time to which you can always go back to at a later point and restore. This is useful if you are making big changes and want to make sure you have a backup of previous versions of your scene.

[Hook](hooks/tk-multi-snapshot/scene_operation_tk-rumba.py) is provided to be able to use this tk-app, similar to workfiles2.

## [tk-multi-loader2](https://support.shotgunsoftware.com/hc/en-us/articles/219033078)
![tk-rumba_01](config/images/tk-rumba_01.png)

The Shotgun Loader lets you quickly overview and browse the files that you have published to Shotgun. A searchable tree view navigation system makes it easy to quickly get to the task, shot or asset that you are looking for and once there the loader shows a thumbnail based overview of all the publishes for that item. Through configurable hooks you can then easily reference or import a publish into your current scene.

[Hook](hooks/tk-multi-loader2/tk-rumba_actions.py) for this tk app supports any PublishedFile that has a Rumba supported extension. You can load Rumba Nodes, and import / reference Alembic caches / USD files, and media (Video File, Movie File, Audio File) that gets loaded into a new media layer in layer manager section of the timeline . [reference, import]
Note that due a current bug, referencing a node that contains references is not supported. Once the Rumba developers solve the issue,  all you need to do is enable 'reference' action type for Rumba Nodes in the configuration yml files.

## [tk-multi-publish2](https://support.shotgunsoftware.com/hc/en-us/articles/115000097513)
![tk-rumba_03](config/images/tk-rumba_03.png)

The Publish app allows artists to publish their work so that it can be used by artists downstream. It supports traditional publishing workflows within the artist’s content creation software as well as stand-alone publishing of any file on disk. When working in content creation software and using the basic Shotgun integration, the app will automatically discover and display items for the artist to publish. For more sophisticated production needs, studios can write custom publish plugins to drive artist workflows.

The basic publishing of the current session is provided as [hooks](hooks/tk-multi-publish2/basic) for this app.

### FBX Animation

Provides the ability to publish the animation as FBX format  as it is supported in Rumba. Note that it will export the whole scene, no support for only selection is provided, please adjust according to your pipeline needs.

Options:
`Export Namespaces`: if True, add a Maya style namespace to each referenced nodes like Maya does with references. The namespace is the name of the Asset root node.

### Alembic Cache

I also provide the ability to publish the animation as Alembic cache format. Note that it will export the whole scene, no support for only selection is provided, please adjust according to your pipeline needs.

Options:
`Sub Samples`: A list of sub-samples to export relative to each frame. If empty, it exports one sample per frame. Values should be between [-1.0, 1.0].
For example, samples=[0.0, 0.4] in a frame range from 1 to 3 would export these  samples : [1.0, 1.4, 2.0, 2.4, 3.0, 3.4].

### USD Stage

Provides a way to publish the current Rumba scene as a USD stage. Note that it will export the whole scene, no support for only selection is provided, please adjust according to your pipeline needs.

### Rumba Node

Finally you can also publish the selected Rumba Node (only the first node in the selection gets published), Be aware though, that only nodes that are not referenced are supported due to a current Bug in Rumba (which would make it crash when referencing those nodes). Once this is resolved the code to update is fairly simple. I will keep an eye on the resolution of this bug and update the hook then.

## [tk-multi-breakdown](https://support.shotgunsoftware.com/hc/en-us/articles/219032988)
![tk-rumba_02](config/images/tk-rumba_02.png)

The Scene Breakdown App shows you a list of items you have loaded (referenced) in your scene and tells you which ones are out of date. Reference nodes or referenced alembic caches are the most common case for Rumba, and their update is supported by this engine. There is also support for updating media loaded in the layer section of the timeline, ie. loading video or audio files.

[Hook](hooks/tk-multi-breakdown/tk-rumba_scene_operations.py) is provided to display the referenced items in the Rumba scene.

## [tk-multi-setframerange](https://support.shotgunsoftware.com/hc/en-us/articles/219033038)
![tk-rumba_05](config/images/tk-rumba_05.png)

This is a simple yet useful app that syncs your current file with the latest frame range in Shotgun for the associated shot. If a change to the cut has come in from editorial, quickly and safely update the scene you are working on using this app. Towards the end, it will display a UI with information about what got changed.

[Hook](hooks/tk-multi-setframerange/frame_operations_tk-rumba.py) is provided to set the frame range within Rumba for a *shot_step* environment.

As always, please adjust this logic accordingly to however you want to handle frame ranges in your pipeline.

## Development notes

The way this engine works is via a [Rumba script](startup/init.py) that is run as soon as Rumba initializes and triggers the instancing of the Rumba toolkit engine. Once the engine is up and running, the [menus](python/tk_rumba/menu_generation.py) are created as normal using PySide widgets, very similar to other engines.

I have to say that this engine turned out to be one of the easiest ones to write, probably becuase PySide is used in the application, I had already quite a lot work done from other engines.

## Rumba development notes

Rumba API is still in its infancy, but this does not mean it is not complete already. I rarely had any issue finding what I needed for the engine hooks. Perhaps not support for events (yet) is something that could be improved, but a handy QTimer does the job for now.

Also, a massive shout out to the Rumba developers, as they were super responsive when I found issues with the API. Custom build with fixes were provided to me whenever an issue was resolved, and promptly after a new release of Rumba itself would follow with the reported issue and others properly addressed. Their Discord channel is super useful and people from Rumba are always there and are very very responsive and attentive.

[Rumba Discord channel](https://discord.com/invite/eRQbxw6)

***

For completion, I've kept the original README from shotgun, that include very valuable links:

## Documentation
This repository is a part of the Shotgun Pipeline Toolkit.

- For more information about this app and for release notes, *see the wiki section*.
- For general information and documentation, click here: https://support.shotgunsoftware.com/entries/95441257
- For information about Shotgun in general, click here: http://www.shotgunsoftware.com/toolkit

## Using this app in your Setup
All the apps that are part of our standard app suite are pushed to our App Store.
This is where you typically go if you want to install an app into a project you are
working on. For an overview of all the Apps and Engines in the Toolkit App Store,
click here: https://support.shotgunsoftware.com/entries/95441247.

## Have a Question?
Don't hesitate to contact us! You can find us on support@shotgunsoftware.com
