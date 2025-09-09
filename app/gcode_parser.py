# Diagnostic message templates for consistency/localization
MESSAGES = {
    'unsupported_g': "Unsupported G-code {code}",
    'unsupported_m': "Unsupported M-code {code}",
    'unknown_param': "Unknown parameter letter '{letter}' in '{word}'",
    'invalid_numeric': "Invalid numeric value for '{letter}': '{bad}'",
    'invalid_word': "Invalid word format: '{word}'",
    'invalid_layer_comment': 'Invalid layer comment format',
    'arc_requirements': 'Arc (G2/G3) requires R>0 or appropriate I/J/K values (per plane).',
}

def parse_gcode(code):
    """
    G-code metnini ayrıştırır ve yolları/layer bilgilerini döndürür.
    Modal komutlar, birim sistemi, koordinat sistemi ve spindle durumu gibi CNC modalitelerini izler.

    Contract:
    - Input: code (str)
    - Output: dict with keys:
        - 'paths': list[dict]  -> hareketler (rapid/feed/arc) ve tanılar (parse_error/unsupported/unknown_param vs.)
        - 'layers': list[dict] -> layer bilgileri
    - Her entry mümkünse 'line_no' ve 'line' (raw) içerir. Tanılar ek olarak 'message' içerir.
    """
    paths: list[dict] = []
    layers: list[dict] = []
    lines = code.splitlines()

    x, y, z = 0.0, 0.0, 0.0
    prev_x, prev_y, prev_z = 0.0, 0.0, 0.0
    unit_scale = 1.0  # mm
    absolute_mode = True
    current_modal = {
        'motion': 'G0',
        'plane': 'G17',
        'units': 'G21',
        'feed_mode': 'G94',
        'coord_system': 'G54',
        'spindle': None,
    }
    current_layer = None

    def update_position(new_x, new_y, new_z):
        nonlocal x, y, z, prev_x, prev_y, prev_z
        prev_x, prev_y, prev_z = x, y, z
        if absolute_mode:
            x, y, z = new_x, new_y, new_z
        else:
            x, y, z = x + new_x, y + new_y, z + new_z
        return x, y, z

    def add_diag(dtype: str, message: str, line_no: int, original_line: str, **extra):
        entry = {'type': dtype, 'message': message, 'line_no': line_no, 'line': original_line}
        entry.update(extra)
        paths.append(entry)

    for line_no, raw_line in enumerate(lines, start=1):
        original_line = raw_line.strip()
        if original_line.startswith(';LAYER:'):
            try:
                current_layer = int(original_line.split(':', 1)[1])
                layers.append({'layer': current_layer, 'paths': []})
            except Exception:
                add_diag('parse_error', MESSAGES['invalid_layer_comment'], line_no, original_line)
            continue

        # Remove ; comments part
        line = original_line.split(';', 1)[0]
        if not line:
            continue

        # Tokenize into words (Letter + numeric)
        words: list[str] = []
        current = ''
        for ch in line:
            if ch.isalpha():
                if current:
                    words.append(current)
                current = ch
            elif ch.strip():
                current += ch
        if current:
            words.append(current)

        motion_command = None
        params: dict = {}
        line_has_motion = False
        line_has_xyz = False

        for word in words:
            letter = word[0].upper()
            try:
                value = float(word[1:])
                if letter == 'G':
                    gnum = int(value)
                    if gnum in (0, 1, 2, 3):
                        motion_command = f'G{gnum}'
                        current_modal['motion'] = motion_command
                        line_has_motion = True
                    elif gnum == 4:
                        paths.append({'type': 'dwell', 'P': params.get('P', value), 'line': original_line, 'line_no': line_no})
                    elif gnum == 17:
                        current_modal['plane'] = 'G17'
                    elif gnum == 18:
                        current_modal['plane'] = 'G18'
                    elif gnum == 19:
                        current_modal['plane'] = 'G19'
                    elif gnum == 20:
                        current_modal['units'] = 'G20'
                        unit_scale = 25.4
                    elif gnum == 21:
                        current_modal['units'] = 'G21'
                        unit_scale = 1.0
                    elif gnum == 28:
                        paths.append({'type': 'home', 'start': (x, y, z), 'line': original_line, 'line_no': line_no})
                    elif gnum == 90:
                        absolute_mode = True
                    elif gnum == 91:
                        absolute_mode = False
                    elif gnum == 94:
                        current_modal['feed_mode'] = 'G94'
                    elif 54 <= gnum <= 59:
                        current_modal['coord_system'] = f'G{gnum}'
                    else:
                        add_diag('unsupported', MESSAGES['unsupported_g'].format(code=f'G{gnum}'), line_no, original_line, code=f'G{gnum}')
                elif letter == 'M':
                    mnum = int(value)
                    if mnum in (3, 4, 5, 6):
                        current_modal['spindle'] = f'M{mnum}'
                        paths.append({'type': 'spindle', 'code': f'M{mnum}', 'line': original_line, 'line_no': line_no})
                    elif mnum in (0, 1):
                        paths.append({'type': 'pause', 'code': f'M{mnum}', 'line': original_line, 'line_no': line_no})
                    elif mnum == 2:
                        paths.append({'type': 'program_end', 'code': 'M2', 'line': original_line, 'line_no': line_no})
                    elif mnum == 30:
                        paths.append({'type': 'program_end', 'code': 'M30', 'line': original_line, 'line_no': line_no})
                    elif mnum in (7, 8, 9):
                        paths.append({'type': 'coolant', 'code': f'M{mnum}', 'line': original_line, 'line_no': line_no})
                    else:
                        add_diag('unsupported', MESSAGES['unsupported_m'].format(code=f'M{mnum}'), line_no, original_line, code=f'M{mnum}')
                elif letter in ('X', 'Y', 'Z', 'I', 'J', 'K', 'R'):
                    params[letter] = value * unit_scale
                    if letter in ('X', 'Y', 'Z'):
                        line_has_xyz = True
                elif letter in ('F', 'S', 'P', 'E', 'D', 'H', 'L', 'T'):
                    params[letter] = value
                else:
                    add_diag('unknown_param', MESSAGES['unknown_param'].format(letter=letter, word=word), line_no, original_line, param=word)
            except ValueError:
                bad = word[1:] if len(word) > 1 else ''
                add_diag('parse_error', MESSAGES['invalid_numeric'].format(letter=letter, bad=bad), line_no, original_line, word=word, param=letter)
                continue
            except IndexError:
                add_diag('parse_error', MESSAGES['invalid_word'].format(word=word), line_no, original_line, word=word)
                continue

        if not motion_command:
            motion_command = current_modal['motion']

        if (line_has_motion or line_has_xyz) and motion_command in ('G0', 'G1', 'G2', 'G3'):
            new_x = params.get('X') if params.get('X') is not None else x
            new_y = params.get('Y') if params.get('Y') is not None else y
            new_z = params.get('Z') if params.get('Z') is not None else z

            if motion_command in ('G0', 'G1'):
                path_type = 'rapid' if motion_command == 'G0' else 'feed'
                path_obj = {
                    'type': path_type,
                    'start': (x, y, z),
                    'end': (new_x, new_y, new_z),
                    'feed_rate': params.get('F'),
                    'plane': current_modal['plane'],
                    'coord_system': current_modal['coord_system'],
                    'layer': current_layer,
                    'line_no': line_no,
                    'line': original_line,
                }
                paths.append(path_obj)
                if layers:
                    layers[-1]['paths'].append(path_obj)
            else:  # G2/G3
                arc_type = 'clockwise' if motion_command == 'G2' else 'counter_clockwise'
                radius = params.get('R')
                has_i, has_j, has_k = ('I' in params), ('J' in params), ('K' in params)
                i_val = params.get('I') if has_i and isinstance(params.get('I'), (int, float)) else None
                j_val = params.get('J') if has_j and isinstance(params.get('J'), (int, float)) else None
                k_val = params.get('K') if has_k and isinstance(params.get('K'), (int, float)) else None
                plane = current_modal['plane']
                if plane == 'G18':  # XZ
                    crx, cry = (i_val or 0.0), (k_val or 0.0)
                    has_center = has_i or has_k
                elif plane == 'G19':  # YZ
                    crx, cry = (j_val or 0.0), (k_val or 0.0)
                    has_center = has_j or has_k
                else:  # G17
                    crx, cry = (i_val or 0.0), (j_val or 0.0)
                    has_center = has_i or has_j
                if radius is None and has_center:
                    radius = (crx ** 2 + cry ** 2) ** 0.5
                if isinstance(radius, (int, float)) and radius > 0:
                    path_obj = {
                        'type': 'arc',
                        'arc_type': arc_type,
                        'cw': True if arc_type == 'clockwise' else False,
                        'start': (x, y, z),
                        'end': (new_x, new_y, new_z),
                        'center_relative': (crx, cry),
                        'center_ijk': (i_val, j_val, k_val),
                        'radius': radius,
                        'feed_rate': params.get('F'),
                        'plane': plane,
                        'coord_system': current_modal['coord_system'],
                        'layer': current_layer,
                        'line_no': line_no,
                        'line': original_line,
                    }
                    paths.append(path_obj)
                    if layers:
                        layers[-1]['paths'].append(path_obj)
                else:
                    add_diag('parse_error', MESSAGES['arc_requirements'], line_no, original_line, motion=motion_command)

            update_position(new_x, new_y, new_z)

    return {'paths': paths, 'layers': layers}
