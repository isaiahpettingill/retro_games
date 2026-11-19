"""Short-horizon jump planner for controller-only platform tests."""

from emulator import A, B, RIGHT


def plan(geom, flags, state, speed):
    end = (len(geom) - 2) * 16

    def simulate(state, step, jump):
        x, y, vy, q, ground = state
        if jump and ground:
            vy = -24
            ground = 0
        for _ in range(5):
            nx = min(x + step, end)
            floor = geom[x // 16] & 240
            lead = geom[(nx + 4) // 16] & 240
            if lead == 240 or y <= lead + 2 or (x // 16 == nx // 16 and y > floor + 2):
                x = nx
            col = x // 16
            groundlevel = geom[col] & 240
            ledge = (geom[col] & 15) * 16
            vy = min(22, vy + 1)
            total = q + vy
            q = total % 4
            old = y
            y += total // 4
            if y < 20:
                y = 20
                vy = 0
            ground = False
            if vy >= 0:
                for height in (ledge, groundlevel):
                    if height < 240 and old <= height <= y:
                        y = height
                        vy = q = 0
                        ground = True
                        break
            if y >= 232:
                return None
        return x, y, vy, q, ground

    paths = [(state, ())]
    for _ in range(16):
        unique = {}
        for st, path in paths:
            for step, jump in [(speed, False), (speed, True), (0, False), (0, True)]:
                if jump and not st[-1]:
                    continue
                s = simulate(st, step, jump)
                if s is None:
                    continue
                x, y, v, q, ground = s
                rank = x - (9 if ground and flags[x // 16] & 15 == 2 else 0)
                rank -= max(0, y - 190) * 0.55
                key = (x // 5, y // 5, v // 3, ground)
                if key in unique and unique[key][0] >= rank:
                    continue
                unique[key] = (rank, s, path + ((step, jump),))
        if not unique:
            break
        paths = [
            (s, p)
            for _, s, p in sorted(
                unique.values(), key=lambda row: row[0], reverse=True
            )[:18]
        ]
    if not paths or not paths[0][1]:
        return [RIGHT | B | A, B | RIGHT]
    # Prefer a route that ends with a safe landing if it is nearly as fast.
    st, path = max(
        paths, key=lambda v: v[0][0] + (8 if v[0][-1] else 0) - max(v[0][1] - 186, 0)
    )
    out = []
    for step, jump in path[:5]:
        key = B | (RIGHT if step else 0)
        out.append(key | (A if jump else 0))
        out.extend([key] * 4)
    return out
