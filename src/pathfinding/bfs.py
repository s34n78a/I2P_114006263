# checkpoint 3
from collections import deque

def bfs_pathfind(current_map, start, goal, is_blocked):
    if start == goal:
        return [start]

    queue = deque([start])
    came_from = {start: None} # daftar kotak yang sudah dikunjungi

    while queue:
        cx, cy = queue.popleft() # x, y kotak skrg

        for nx, ny in ((cx+1,cy), (cx-1,cy), (cx,cy+1), (cx,cy-1)): # neighbor kotak (kiri, kanan, atas, bawah)
            if (nx, ny) not in came_from and not is_blocked(nx, ny): # cek kalo blm dikunjungi & ga terblokir
                came_from[(nx, ny)] = (cx, cy) # set parent kotak neighbor (kotak skrg: kotak selanjutnya)
                queue.append((nx, ny))

                if (nx, ny) == goal:
                    path = [(nx, ny)]
                    while path[-1] != start:
                        path.append(came_from[path[-1]]) # backtrack dari goal ke start
                    path.reverse()
                    return path

    return None  # no path found
