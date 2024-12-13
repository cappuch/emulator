class CPU:
    def __init__(self):
        self.A = 0
        self.B = 0
        self.PC = 0

        self.memory = [0] * 1024 # 1KB memory

        self.zero_flag = False
        self.carry_flag = False
        
        self.instructions = {
            0x00: self.nop,    # No operation
            0x01: self.lda,    # Load value to A
            0x02: self.add,    # Add value to A
            0x03: self.sub,    # Subtract value from A
            0x04: self.sta,    # Store A to memory
            0x05: self.jmp,    # Jump to address
            0x06: self.jz,     # Jump if zero
            0xFF: self.halt    # Halt CPU
        }
        
        self.running = False

    def load_program(self, program):
        """Load a program into memory"""
        for i, value in enumerate(program):
            self.memory[i] = value

    def fetch(self):
        """Fetch an instruction from memory"""
        instruction = self.memory[self.PC]
        self.PC += 1
        return instruction

    def execute(self, instruction):
        """Execute an instruction"""
        if instruction in self.instructions:
            self.instructions[instruction]()
        else:
            print(f"Unknown instruction: {hex(instruction)}")
            print("Halting!")
            self.running = False
            print("CPU state:")
            self.dump_state()

    def nop(self):
        """No operation"""
        pass

    def lda(self):
        """Load value into accumulator"""
        value = self.memory[self.PC]
        self.PC += 1
        self.A = value
        self.zero_flag = (self.A == 0)

    def add(self):
        """Add value to accumulator"""
        value = self.memory[self.PC]
        self.PC += 1
        result = self.A + value
        self.carry_flag = result > 255
        self.A = result & 0xFF
        self.zero_flag = (self.A == 0)

    def sub(self):
        """Subtract value from accumulator"""
        value = self.memory[self.PC]
        self.PC += 1
        result = self.A - value
        self.carry_flag = result < 0
        self.A = result & 0xFF
        self.zero_flag = (self.A == 0)

    def sta(self):
        """Store accumulator to memory"""
        address = self.memory[self.PC]
        self.PC += 1
        self.memory[address] = self.A

    def jmp(self):
        """Jump to address"""
        address = self.memory[self.PC]
        self.PC = address

    def jz(self):
        """Jump if zero flag is set"""
        address = self.memory[self.PC]
        self.PC += 1
        if self.zero_flag:
            self.PC = address

    def halt(self):
        """Halt the CPU"""
        self.running = False

    def run(self):
        """Run the CPU"""
        self.running = True
        self.PC = 0
        
        while self.running:
            instruction = self.fetch()
            self.execute(instruction)
            
    def dump_state(self):
        """Print CPU state for debugging"""
        print(f"A: {hex(self.A)}, B: {hex(self.B)}, PC: {hex(self.PC)}")
        print(f"Flags - Zero: {self.zero_flag}, Carry: {self.carry_flag}")