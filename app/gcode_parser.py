def parse_gcode(code):
    """
    G-code metnini ayrıştırır ve yolları/layer bilgilerini döndürür.
    Modal komutlar, birim sistemi, koordinat sistemi ve spindle durumu gibi CNC modalitelerini izler.
    :param code: str, G-code metni
    :return: dict, {'paths': [...], 'layers': [...]}
    """
    """G-code parser with modal commands and unit system support"""
    paths = []
    layers = []  # Katman bilgisi için
    lines = code.splitlines()
    x, y, z = 0, 0, 0  # Current position
    prev_x, prev_y, prev_z = 0, 0, 0  # Previous position
    unit_scale = 1.0  # Default mm
    absolute_mode = True
    current_modal = {
        'motion': 'G0',  # G0, G1, G2, G3
        'plane': 'G17',  # G17, G18, G19
        'units': 'G21',  # mm
        'feed_mode': 'G94',  # units per minute
        'coord_system': 'G54',  # Default coordinate system
        'spindle': None,  # M3, M5, M6
    }
    current_layer = None

    def update_position(new_x, new_y, new_z):
        """
        CNC pozisyonunu günceller.
        :param new_x: float
        :param new_y: float
        :param new_z: float
        :return: tuple, yeni (x, y, z)
        """
        nonlocal x, y, z, prev_x, prev_y, prev_z
        prev_x, prev_y, prev_z = x, y, z
        if absolute_mode:
            x, y, z = new_x, new_y, new_z
        else:
            x += new_x
            y += new_y
            z += new_z
        return x, y, z

    for line in lines:
        """
        Her satırı işler, layer ve G-code komutlarını ayrıştırır.
        """
        original_line = line.strip()
        # Katman/LAYER yorumlarını yakala
        if original_line.startswith(';LAYER:'):
            try:
                current_layer = int(original_line.split(':')[1])
                layers.append({'layer': current_layer, 'paths': []})
            except Exception:
                print(f"Warning: Invalid layer comment: {original_line}")
            continue
        # Satırdan yorumları kaldır
        line = original_line.split(';')[0]
        if not line:
            continue

        words = []
        current_word = ''

        # Parse line into G-code words
        for char in line:
            if char.isalpha():
                if current_word:
                    words.append(current_word)
                current_word = char
            elif char.strip():
                current_word += char
        if current_word:
            words.append(current_word)

        motion_command = None
        params = {}

        for word in words:
            letter = word[0].upper()
            try:
                value = float(word[1:])
                if letter == 'G':
                    code = int(float(word[1:]))
                    if code in [0, 1, 2, 3]:
                        motion_command = f'G{code}'
                        current_modal['motion'] = motion_command
                    elif code == 4:
                        # G4: Dwell (bekleme)
                        paths.append({'type': 'dwell', 'P': params.get('P', value), 'line': original_line})
                    elif code == 17:
                        current_modal['plane'] = 'G17'  # XY
                    elif code == 18:
                        current_modal['plane'] = 'G18'  # XZ
                    elif code == 19:
                        current_modal['plane'] = 'G19'  # YZ
                    elif code == 20:
                        current_modal['units'] = 'G20'
                        unit_scale = 25.4  # inch to mm
                    elif code == 21:
                        current_modal['units'] = 'G21'
                        unit_scale = 1.0
                    elif code == 28:
                        # G28: Home
                        paths.append({'type': 'home', 'start': (x, y, z), 'line': original_line})
                    elif code == 90:
                        absolute_mode = True
                    elif code == 91:
                        absolute_mode = False
                    elif code == 94:
                        # G94: Feed per minute (modal)
                        current_modal['feed_mode'] = 'G94'
                        # Not an unsupported command, just update modal state
                    elif 54 <= code <= 59:
                        current_modal['coord_system'] = f'G{code}'
                    else:
                        print(f"Warning: Unsupported G-code: G{code} in line: {original_line}")
                        paths.append({'type': 'unsupported', 'code': f'G{code}', 'line': original_line})
                elif letter == 'M':
                    mcode = int(float(word[1:]))
                    if mcode in [3, 4, 5, 6]:
                        current_modal['spindle'] = f'M{mcode}'
                        paths.append({'type': 'spindle', 'code': f'M{mcode}', 'line': original_line})
                    elif mcode == 30:
                        # M30: Program end (not unsupported, just mark)
                        paths.append({'type': 'program_end', 'code': 'M30', 'line': original_line})
                    else:
                        print(f"Warning: Unsupported M-code: M{mcode} in line: {original_line}")
                        paths.append({'type': 'unsupported', 'code': f'M{mcode}', 'line': original_line})
                elif letter in ['X', 'Y', 'Z', 'I', 'J', 'R']:
                    params[letter] = value * unit_scale
                elif letter in ['F', 'S', 'P', 'Q', 'E', 'D', 'H', 'L', 'T']:
                    params[letter] = value
                else:
                    print(f"Warning: Unknown parameter: {word} in line: {original_line}")
                    paths.append({'type': 'unknown_param', 'param': word, 'line': original_line})
            except ValueError:
                print(f"Warning: Invalid value in word: {word} in line: {original_line}")
                paths.append({'type': 'parse_error', 'word': word, 'line': original_line})
                continue
            except IndexError:
                print(f"Warning: Invalid word format: {word} in line: {original_line}")
                paths.append({'type': 'parse_error', 'word': word, 'line': original_line})
                continue


        # Use modal motion command if none specified
        if not motion_command:
            motion_command = current_modal['motion']

        # Process motion command
        if motion_command in ['G0', 'G1', 'G2', 'G3']:
            new_x = params.get('X') if params.get('X') is not None else x
            new_y = params.get('Y') if params.get('Y') is not None else y
            new_z = params.get('Z') if params.get('Z') is not None else z

            if motion_command in ['G0', 'G1']:
                path_type = 'rapid' if motion_command == 'G0' else 'feed'
                path_obj = {
                    'type': path_type,
                    'start': (x, y, z),
                    'end': (new_x, new_y, new_z),
                    'feed_rate': params.get('F'),
                    'plane': current_modal['plane'],
                    'coord_system': current_modal['coord_system'],
                    'layer': current_layer
                }
                paths.append(path_obj)
                if layers:
                    layers[-1]['paths'].append(path_obj)
            elif motion_command in ['G2', 'G3']:
                arc_type = 'clockwise' if motion_command == 'G2' else 'counter_clockwise'
                radius = params.get('R')
                i_val = params.get('I') if isinstance(params.get('I'), (int, float)) else 0
                j_val = params.get('J') if isinstance(params.get('J'), (int, float)) else 0
                # Only calculate radius if both I and J are numbers (not None)
                if radius is None and (isinstance(i_val, (int, float)) and isinstance(j_val, (int, float))):
                    radius = (i_val**2 + j_val**2)**0.5
                if isinstance(radius, (int, float)):
                    path_obj = {
                        'type': 'arc',
                        'arc_type': arc_type,
                        'start': (x, y, z),
                        'end': (new_x, new_y, new_z),
                        'center_relative': (i_val, j_val),
                        'radius': radius,
                        'feed_rate': params.get('F'),
                        'plane': current_modal['plane'],
                        'coord_system': current_modal['coord_system'],
                        'layer': current_layer
                    }
                    paths.append(path_obj)
                    if layers:
                        layers[-1]['paths'].append(path_obj)

            update_position(new_x, new_y, new_z)

    return {'paths': paths, 'layers': layers}
    """
    Yollar ve layer bilgilerini içeren sözlük döndürülür.
    """
