# Labradorite Lattice

Full-colour Python 3 neon pipe-flow arcade for [ElbowOS](https://x.com/ElbowOS).

Rotate conduit tiles so molten gold can cross the iridescent lattice. Straight and elbow veins start misaligned. The flow leaks if a tile is still wrong when the head arrives. Clearing a board banks a bonus and deals a new lattice.

This is an original pipe-flow game. It is not a Nintendo ROM, not an emulator, and not a copy of the other ElbowOS packs.

## Play

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 labradorite_lattice.py --play
```

Controls: arrows or WASD move the cursor, Space or click rotates a tile, R restarts.

Needs Python 3.10+ and a desktop window (pygame + SDL).

## Record a 9:16 reel

```bash
python3 labradorite_lattice.py --record
```

Headless path uses `SDL_VIDEODRIVER=dummy`, draws 1080x1920 at 30 fps for 15 seconds, and pipes RGB frames to ffmpeg (libx264, yuv420p, CRF 20, +faststart).

## Links

- Featured account: https://x.com/ElbowOS
- Drive reel: https://drive.google.com/file/d/1qc4XPPU1qzGkFhFY7yqJVzy2B9yveh-5/view
- The MP4 is not posted to X from this pack. Attach the Drive file manually on https://x.com/ElbowOS.
