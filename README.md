This project is based on this project by 0CottonBuds: https://github.com/0CottonBuds/Osu-Most-Played-Beatmap-Downloader/tree/6fd740f03136c55bb908fbbb921af8783eb839a7

This program will automatically download all of your osu! top plays and store them in a folder.

HOW TO USE:
1. Install python (https://www.python.org/downloads/)
2. Download main.py and put it in a folder you want to store you maps into.
4. Get your osu! user id:
   Go to your profile and copy the numbers at the end of the URL, this is your user id.
   EXAMPLE: https://osu.ppy.sh/users/22845738 --> 22845738 is your user id.
   Open main.py and edit the script on line 143 to fill in your user id.
5. Get your osu! client id and client secret:
   Go to your account settings on the osu website, scroll to OAuth and click New OAuth Application and name it anything you want.
   Then copy your client id and paste this into line 11 in main.py
   Also copy your client secret (do not show this to anyone) and paste this into line 12 in main.py
6. In file explorer, go into the folder where you put main.py, and click on the bar that shows your file path which is above all your files. Click on this, and type cmd.
7. In cmd, type: pip install requests
8. Then type: python main.py
9. It will start downloading your top plays (it's a bit slow) and it will put it into a downloads folder inside the folder where main.py is.
