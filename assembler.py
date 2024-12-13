from archi import CPU
from gpu import GPU

class Assembler:
    def __init__(self):
        self.cpu_instructions = {
            'NOP': 0x00,
            'LDA': 0x01,
            'ADD': 0x02,
            'SUB': 0x03,
            'STA': 0x04,
            'JMP': 0x05,
            'JZ':  0x06,
            'HALT': 0xFF
        }
        
        self.gpu_instructions = {
            'GNOP': 0x00,
            'SETX': 0x01,
            'SETY': 0x02,
            'SETC': 0x03,
            'PLOT': 0x04,
            'CLEAR': 0x05,
            'LINE': 0x06,
            'RECT': 0x07,
            'GHALT': 0xFF
        }
        
        self.symbols = {}
        
    def is_number(self, s):
        try:
            if s.startswith('0x'):
                int(s, 16)
            elif s.startswith('0b'):
                int(s, 2)
            else:
                int(s)
            return True
        except ValueError:
            return False

    def parse_value(self, s):
        if s.startswith('0x'):
            return int(s, 16)
        elif s.startswith('0b'):
            return int(s, 2)
        else:
            return int(s)

    def assemble(self, source):
        lines = source.split('\n')
        cleaned_lines = []
        current_address = 0
        mode = 'CPU'
        
        for line in lines:
            line = line.split(';')[0].strip()
            if not line:
                continue

            if line.startswith('.'):
                directive = line[1:].upper()
                if directive in ['CPU', 'GPU']:
                    mode = directive
                    cleaned_lines.append((mode, line))
                    continue
                else:
                    raise ValueError(f"Unknown directive: {line}")

            if ':' in line:
                label, rest = line.split(':', 1)
                label = label.strip()
                self.symbols[label] = current_address
                line = rest.strip()
                if not line:
                    continue
            
            cleaned_lines.append((mode, line))
            parts = line.split()
            current_address += 1
            if len(parts) > 1:
                current_address += len(parts) - 1

        machine_code = []
        mode = 'CPU'
        for stored_mode, line in cleaned_lines:
            if line.startswith('.'):
                mode = stored_mode
                continue
                
            parts = line.split()
            instruction = parts[0].upper()

            instruction_set = self.cpu_instructions if mode == 'CPU' else self.gpu_instructions
            
            if instruction not in instruction_set:
                raise ValueError(f"Unknown {mode} instruction: {instruction}")
            
            machine_code.append(instruction_set[instruction])

            if len(parts) > 1:
                for operand in parts[1:]:
                    if self.is_number(operand):
                        value = self.parse_value(operand)
                        if value > 255:
                            raise ValueError(f"Operand value too large: {operand}")
                        machine_code.append(value)
                    elif operand in self.symbols:
                        machine_code.append(self.symbols[operand])
                    else:
                        raise ValueError(f"Unknown operand: {operand}")
        
        return machine_code

if __name__ == "__main__":
    program = """
        ; CPU Section
        .CPU
        LDA 5           ; Load 5 into accumulator
        STA 0x20       ; Store it in memory
        
        ; GPU Section
        .GPU
        CLEAR          ; Clear the screen
        SETC 1        ; Set color to white
        SETX 10       ; Set X coordinate
        SETY 10       ; Set Y coordinate
        RECT 20 20    ; Draw 20x20 rectangle
        LINE 50 50    ; Draw line to (50,50)
        GHALT         ; Stop GPU
        
        ; Back to CPU
        .CPU
        HALT          ; Stop CPU
        ; I don't really know how to write assembly.
    """
    
    assembler = Assembler()
    cpu = CPU()
    gpu = GPU()
    
    try:
        machine_code = assembler.assemble(program)
        print("Machine code:", [hex(x) for x in machine_code])

        cpu_code = []
        gpu_code = []
        current_code = cpu_code
        mode = 'CPU'
        
        i = 0
        while i < len(machine_code):
            instruction = machine_code[i]

            if instruction in assembler.cpu_instructions.values():
                if mode != 'CPU':
                    mode = 'CPU'
                    current_code = cpu_code
                current_code.append(instruction)

                if instruction != 0xFF and instruction != 0x00:
                    i += 1
                    if i < len(machine_code):
                        current_code.append(machine_code[i])

            elif instruction in assembler.gpu_instructions.values():
                if mode != 'GPU':
                    mode = 'GPU'
                    current_code = gpu_code
                current_code.append(instruction)
                if instruction == 0x07:
                    i += 1
                    current_code.extend(machine_code[i:i+2])
                    i += 1
                elif instruction == 0x06:
                    i += 1
                    current_code.extend(machine_code[i:i+2])
                    i += 1
                elif instruction not in [0x00, 0xFF, 0x04, 0x05]:
                    i += 1
                    if i < len(machine_code):
                        current_code.append(machine_code[i])
            
            i += 1

        if cpu_code:
            print("Running CPU code:", [hex(x) for x in cpu_code])
            cpu.load_program(cpu_code)
            cpu.run()
            cpu.dump_state()

        if gpu_code:
            print("Running GPU code:", [hex(x) for x in gpu_code])
            gpu.load_program(gpu_code)
            gpu.run()
            gpu.display()
        
    except ValueError as e:
        print(f"Assembly error: {e}")