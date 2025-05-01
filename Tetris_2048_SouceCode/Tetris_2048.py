
#!/usr/bin/env python3

import threading, subprocess, time
import stddraw, random, os
from game_grid    import GameGrid
from tetromino    import Tetromino
from picture      import Picture
from color        import Color
from achievements import AchievementManager

# Achievements & Music
ach_mgr = AchievementManager()
stop_bgm = threading.Event()
def _play_bgm_loop():
    while not stop_bgm.is_set():
        p = subprocess.Popen(['afplay','bgm.wav'])
        while p.poll() is None and not stop_bgm.is_set():
            time.sleep(0.1)
        if stop_bgm.is_set():
            p.terminate()
            break
threading.Thread(target=_play_bgm_loop, daemon=True).start()

# Helpers
def rowsToCheck(tiles):
    return {t.position.y for row in tiles for t in row if t}
def colsToCheck(tiles):
    return {t.position.x for row in tiles for t in row if t}
def create_tetromino(h, w):
    return Tetromino(random.choice(['I','O','Z']), h, w)

# Main
def start():
    grid_h, grid_w = 20, 12
    extra_cols     = 4

    # Canvas & scale
    stddraw.setCanvasSize(40*(grid_w+extra_cols), 40*grid_h)
    stddraw.setXscale(-0.5, grid_w+extra_cols-0.5)
    stddraw.setYscale(-0.5, grid_h-0.5)

    # Sidebar geometry
    panel_x     = grid_w + extra_cols/2
    panel_hw    = extra_cols/2
    btn_hw, btn_hh = panel_hw - 0.2, 0.8
    py_pause    = grid_h - 3
    py_score    = py_pause - 3
    py_next_btn = py_score - 3

    # Colors
    bg, btn_c, txt_c     = Color(42,69,99), Color(25,255,228), Color(31,160,239)
    side_bg, side_tx     = Color(205,193,180), Color(119,110,101)
    ghost_c              = Color(150,150,150)

    # State
    paused     = False
    show_next  = True
    prev_mouse = False

    # 1) MENU SCREEN
    stddraw.clear(bg)
    pic = Picture(os.path.join(os.path.dirname(__file__),'menu_image.png'))
    stddraw.picture(pic, (grid_w-1)/2, grid_h-7)
    mx, my = (grid_w-1)/2, 3.5
    stddraw.setPenColor(btn_c)
    stddraw.filledRectangle(mx, my, 4, 1.5)
    stddraw.setFontFamily('Arial'); stddraw.setFontSize(25)
    stddraw.setPenColor(txt_c)
    stddraw.text(mx, my, 'Click to Start')
    while True:
        stddraw.show(300)
        if stddraw.mousePressed():
            x, y = stddraw.mouseX(), stddraw.mouseY()
            if abs(x-mx)<=4 and abs(y-my)<=1.5:
                break

    # 2) INITIALIZE GAME
    grid       = GameGrid(grid_h, grid_w)
    current    = create_tetromino(grid_h, grid_w)
    current.move('down', grid)
    next_piece = create_tetromino(grid_h, grid_w)
    game_over  = False

    # 3) MAIN GAME LOOP
    while not game_over:
        grid.current_tetromino = current

        # DROP + RENDER LOOP
        while True:
            # edge-detect clicks and consume until release
            m = stddraw.mousePressed()
            if m and not prev_mouse:
                x, y = stddraw.mouseX(), stddraw.mouseY()
                # Pause toggle
                if abs(x-panel_x)<=btn_hw and abs(y-py_pause)<=btn_hh:
                    paused = not paused
                # Next toggle
                if abs(x-panel_x)<=btn_hw and abs(y-py_next_btn)<=btn_hh:
                    show_next = not show_next
                # wait until release
                while stddraw.mousePressed():
                    stddraw.show(50)
                prev_mouse = False
            else:
                prev_mouse = m

            # handle keyboard when running
            if not paused and stddraw.hasNextKeyTyped():
                k = stddraw.nextKeyTyped()
                if k in ('left','right','down','up','space'):
                    current.move(k, grid)

            # draw
            stddraw.clear(bg)
            grid.draw_grid()

            # ghost piece
            dmin=grid.grid_height
            for row in current.tile_matrix:
                for t in row:
                    if t:
                        x0,y0=t.position.x,t.position.y; d=0
                        while grid.is_inside(y0-d-1,x0) and not grid.is_occupied(y0-d-1,x0):
                            d+=1
                        dmin=min(dmin,d)
            stddraw.setPenColor(ghost_c)
            for row in current.tile_matrix:
                for t in row:
                    if t:
                        stddraw.filledSquare(t.position.x,t.position.y-dmin,0.5)

            # actual piece
            for row in current.tile_matrix:
                for t in row:
                    if t:
                        stddraw.setPenColor(t.background_color)
                        stddraw.filledSquare(t.position.x,t.position.y,0.5)
                        stddraw.setPenColor(t.boundary_color)
                        stddraw.square(t.position.x,t.position.y,0.5)
                        stddraw.setFontFamily('Arial'); stddraw.setFontSize(16)
                        stddraw.setPenColor(t.foreground_color)
                        stddraw.boldText(t.position.x,t.position.y,str(t.number))

            grid.draw_boundaries()

            # sidebar
            stddraw.setPenColor(side_bg)
            stddraw.filledRectangle(panel_x,grid_h/2,panel_hw,grid_h/2)

            # pause button
            stddraw.setPenColor(btn_c)
            stddraw.filledRectangle(panel_x,py_pause,btn_hw,btn_hh)
            stddraw.setFontFamily('Arial'); stddraw.setFontSize(20)
            stddraw.setPenColor(txt_c)
            stddraw.text(panel_x,py_pause,'⏸' if not paused else '▶')

            # score
            stddraw.setFontFamily('Arial'); stddraw.setFontSize(18)
            stddraw.setPenColor(Color(255,255,255))
            stddraw.text(panel_x,py_score,'Score')
            stddraw.setFontSize(24)
            stddraw.text(panel_x,py_score-1.5,str(grid.score))

            # Show Next Piece button
            stddraw.setPenColor(btn_c)
            stddraw.filledRectangle(panel_x,py_next_btn,btn_hw,btn_hh)
            stddraw.setFontFamily('Arial'); stddraw.setFontSize(14)
            stddraw.setPenColor(txt_c)
            stddraw.text(panel_x,py_next_btn,'Show Next Piece')

            # Next preview (correct orientation)
            if show_next:
                oy=py_next_btn-btn_hh-2
                mat=next_piece.tile_matrix
                rows=len(mat); cols=len(mat[0])
                for i in range(rows):
                    for j in range(cols):
                        t=mat[i][j]
                        if t:
                            px=panel_x+(j-(cols-1)/2)
                            py=oy+((rows-1)/2 - i)
                            stddraw.setPenColor(t.background_color)
                            stddraw.filledSquare(px,py,0.4)
                            stddraw.setPenColor(t.boundary_color)
                            stddraw.square(px,py,0.4)
                            stddraw.setFontFamily('Arial'); stddraw.setFontSize(12)
                            stddraw.setPenColor(t.foreground_color)
                            stddraw.boldText(px,py,str(t.number))

            # frame delay
            stddraw.show(300)

            if paused:
                continue

            if not current.move('down',grid):
                break

        # place & checks
        tiles=current.tile_matrix
        game_over=grid.update_grid(tiles)
        rows=rowsToCheck(tiles); grid.rowCheck(rows)
        if rows: ach_mgr.report_event('row_cleared',len(rows))
        cols=colsToCheck(tiles); grid.sumCheck(cols,current)
        ach_mgr.report_event('score_update',grid.score)
        if game_over: break

        current=next_piece
        next_piece=create_tetromino(grid_h,grid_w)

    # GAME OVER
    stop_bgm.set()
    stddraw.clear(bg)
    stddraw.setFontFamily('Arial'); stddraw.setFontSize(40)
    stddraw.setPenColor(Color(255,255,255))
    stddraw.text((grid_w-1)/2,grid_h/2,'Game Over')
    stddraw.setFontSize(24)
    stddraw.text((grid_w-1)/2,grid_h/2-2,f'Score: {grid.score}')
    stddraw.show(0)
    stddraw.mainloop()

if __name__=='__main__':
    start()
