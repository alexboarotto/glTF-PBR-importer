# glTF-PBR-importer
Add-On that imports json file containing PBR data not supported by glTF and recreates it in Blender

## Installation
Download this repo as a zip file clicking on Code > Download ZIP

![image](https://user-images.githubusercontent.com/59767130/167828490-cd619e06-9eec-430b-93b9-6dd42185c01d.png)

Copy the **PBR-Importer** folder into your Blender *"addons"* directory (In Windows it's usually C:\Program Files\Blender Foundation\Blender 3.0\3.0\scripts\addons)
To find the Blender directory on your system check out: https://docs.blender.org/manual/en/latest/advanced/blender_directory_layout.html

In Blender, go to Edit > Preferences > Add-Ons and search for **"Import-Export: glTF PBR Importer"**

![image](https://user-images.githubusercontent.com/59767130/167828936-7f9539fb-9c81-4e80-97dc-8088cddd2ee9.png)

Activate it by clicking on the checkbox

## UI
In the properties panel open the scene tab. There you will find a Header called *"Import PBR Data"*. Click on it to see the plugin's UI.

![image](https://user-images.githubusercontent.com/59767130/167829304-8ec87db6-3a00-41c5-b582-1e1451cd4e1c.png)

![image](https://user-images.githubusercontent.com/59767130/167829354-49a2d42e-196c-40d4-9fe5-bc247cda4d0f.png)

- The _Import JSON_ button will open a file browser where you will be able to select the .json file containing the data related to the scene.
- The _Create Scene_ button will import all objects defined in the json file and their respective textures and material data.

## Rendering
To Render the scene we may have to chenge some of Blender's render settings. First off let's make sure the **render engine** is set to ***Cycles***. To do so go to the render properties tab and make sure that Cycles is selected in the dropdown menu.

![image](https://user-images.githubusercontent.com/59767130/167830619-e4896c6d-afc4-4ca2-ad9b-7511ea6db9d2.png)

If you have a graphics card installed on your system you can choose to render with *GPU acceleration*

![image](https://user-images.githubusercontent.com/59767130/167830944-2b7de9a9-15f6-4d8c-995b-4df6c2b24ecc.png)

Now let's change the Output settings.
First let's change the output **resolution** to whatever we'd like (default is *1920 x 1080*)

![image](https://user-images.githubusercontent.com/59767130/167831752-9beaa779-929e-430d-b3dd-3a59ca7bae08.png)

Then choose the **directory** where you'd like the render to be saved. 

![image](https://user-images.githubusercontent.com/59767130/167831911-13d9f3df-b2a8-4eef-bb7e-a89225345610.png)

The scene is now ready to be rendered. Feel free to mess around with the settings as much as you'd like!



