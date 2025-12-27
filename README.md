This project is based on another project by 0CottonBuds: https://github.com/0CottonBuds/Osu-Most-Played-Beatmap-Downloader/tree/6fd740f03136c55bb908fbbb921af8783eb839a7

This program will automatically download all of your osu! top plays and store them in a folder.
Works on any mode.

HOW TO USE:
1. Install python (https://www.python.org/downloads/)
2. Download main.py and put it in a folder you want to store you maps into.
3. In file explorer, go into the folder where you put main.py, and click on the bar that shows your file path which is above all your files. Click on this, and type cmd.
4. In cmd, type: pip install requests
5. Then type: python main.py, it will now ask questions to get the necessary information
6. Get your osu! user id:
   Go to your profile and copy the numbers at the end of the URL, this is your user id.
   EXAMPLE: https://osu.ppy.sh/users/22845738 --> 22845738 is your user id.
7. Get your osu! client id and client secret:
   Go to your account settings on the osu website, scroll to OAuth and click New OAuth Application and name it anything you want. It will show your client id and your client secret.
8. Choose the mode you want
9. Choose the amount of maps you want to download (200 = all your top plays)
10. It will start downloading your top plays (it's a bit slow) and it will put it into the folder where main.py is.
