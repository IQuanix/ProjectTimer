# Project Timer

A lightweight app to track the time you spend on Projects.<br>
Yeah it was mostly vibe coded, take it or leave it.<br>
(Qt/PySide6 interface)

## Current features
- Keep time on projects you work on.
- Start/stop and restart timer controls.
- Add/edit/remove projects.
- Resizable fixed-ratio window.
- Toggleable project list view with rows for better overview.
- Always-on-top toggle.
- Theme builder.
>- Option to copy/create/edit themes
>- Option to toggle the background animation
>- Option to add background images
>- Option for simple Glass-UI
>- Option to make the window seethrough
>- Option for blurring the background with gaussian/directional blur
>- Many colors to choose from
- Archive for deleted projects.
- Editable `.csv`
- Editable icons
- Editable `.json`



## Installation
Currently a single executable that creates starting folders by itself if none are there.<br>
Just open the .exe, done.

## Customizing the App
This app was coded with customizability in mind.<br>

Want to change the colors?<br>
>Just use the Theme Builder and choose from many colors and  shades.<br>
>No exact color you want? Paste in the hex-code!

Don't like the themes?<br>
>Create new ones, name them and edit until you like it.<br>
>(Pro tip: you can copy a theme so you don't start from nothing)

Size of the window to small?<br>
>Scale it up or down.

One Project is not enough?<br>
>You can add as many as you like.<br>
>Change to list-view if you need a better overview.<br>

Don't like the animation or want to add your own background?
>Change animation-visibility or the background image in the Theme Builder (per theme)

Want a custom background?
>Just drop some into the `backgrounds` folder!<br>
>_Supported file-types:_
>- `.png`
>- `.jpg`
>- `.jpeg`
>- `.webp`
>- `.bmp`

Want different fonts?
>Drop new ones into `fonts`
>You can change the size to fit each theme!<br>
>Default font:`Segoe UI`<br>
>_Supported file-types:_
>- `.ttf`
>- `.otf`
>- `.ttc`


## Data files
Project times are saved in `data\projects.csv`.<br>
If you deleted something it always goes into the archive in `data\archive.csv`.<br>
You can edit the `project.csv` directly if you have more then a few projects or a backup-file. <br>
Time is written as `HH:MM:SS`.<br>

**Formatting:** <br>
|A|B|
|----|----|
|Name|00:00:00|

>_example:_<br>
>|A|B|
>|----|----|
>|Client Work|01:25:10|

## Config files
Settings for all themes sit in `config\themes.json`.<br>
Settings for latest states like window_scale sit in `config\settings.json`.<br>

## Icon files
All icons can be changed, but apply globally.<br>
When changing make sure to have a clean black icon as a `.ico` file and keep the names the same.<br>
If icons are deleted or a name is not matching, a fresh one will be added again after startup.

