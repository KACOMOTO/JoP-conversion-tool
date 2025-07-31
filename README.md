# JoP Conversion Tool

**JoP Conversion Tool** is a standalone utility for the Minecraft mod [Joy of Painting](https://www.curseforge.com/minecraft/mc-mods/joy-of-painting).

This tool allows you to convert PNG images into `.paint` files that can be imported as in-game paintings using the `/paintingimport` command.

To use it, simply **download the `.exe` file and run it** — no installation or Python required.

The tool provides:
- Export of single or split paintings
- Automatic tiling and canvas fitting
- Visual interface for canvas size and layout
- Fully self-contained executable

Paintings exported with this utility can be placed in your Minecraft world using the mod.

## 🖥 How to Use

1. **Launch** the tool (no installation required)
2. Click **Open PNG** and select your image
3. Choose mode: **Single Canvas** or **Split**
4. Set tile or canvas size and grid width. And set author and name of the painting.
5. Click **Export**
6. Select your .minecraft/paintings directory
7. Resulting `.paint` files will be created in the output folder
8. Check the names of wanted painting and copy it. 
9. In-game, type `/paintingimport <painting_name>` into the chat — for example, `/paintingimport painting_1` — to import your painting.  
**Note:** If you're in Survival mode, you must hold a canvas in your main hand for the command to work.
10. Enjoy your painting.
P.S. If u used `Split` — there will be several files with name of the paintings with numerical suffix (e.g. painting_1, painting_2 etc.), you'll need to manually repeat step 9 for all of them ;D
