"""CPU functionality."""

import sys

SP = 7

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 256
        self.reg = [0] * 8   # RO-R7
        self.pc = 0
        self.reg[SP] = 0xF4
        self.branch_table = {
            0b10000010: self.LDI,
            0b01000111: self.PRN,
            0b10100000: self.ADD,
            0b10100010: self.MUL,
            0b01000101: self.PUSH,
            0b01000110: self.POP,
            0b01010000: self.CALL,
            0b00010001: self.RET,
            0b10100111: self.CMP,
            0b01010100: self.JMP,
            0b01010101: self.JEQ,
            0b01010110: self.JNE,
        }
        self.fl = 0
        self.running = True

    def ram_read(self, MAR):
        return self.ram[MAR]

    def ram_write(self, MAR, MDR):
        self.ram[MAR] = MDR

    def load(self):
        """Load a program into memory."""

        # address = 0
        #
        # # For now, we've just hardcoded a program:
        #
        # program = [
        #     # From print8.ls8
        #     0b10000010, # LDI R0,8
        #     0b00000000,
        #     0b00001000,
        #     0b01000111, # PRN R0
        #     0b00000000,
        #     0b00000001, # HLT
        # ]
        #
        # for instruction in program:
        #     self.ram[address] = instruction
        #     address += 1

        if len(sys.argv) != 2:
            print("usage: python3 ls8.py examples/mult.ls8")
            sys.exit(1)

        address = 0

        try:
            with open(sys.argv[1]) as f:
                for line in f:
                    line_value = line.split("#")[0].strip()
                    if line_value == '':
                        continue
                    val = int(line_value, 2)
                    self.ram[address] = val
                    address += 1

        except FileNotFoundError:
            print(f"File not found: {sys.argv[1]}")
            sys.exit(2)

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        #elif op == "SUB": etc
        elif op == "MUL":
            self.reg[reg_a] *= self.reg[reg_b]
        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def HLT(self, operand_a, operand_b):
        self.running = False

    def LDI(self, operand_a, operand_b):
        self.reg[operand_a] = operand_b

    def PRN(self, operand_a, operand_b):
        print(self.reg[operand_a])

    def ADD(self, operand_a, operand_b):
        self.reg[operand_a] += self.reg[operand_b]

    def MUL(self, operand_a, operand_b):
        self.reg[operand_a] *= self.reg[operand_b]

    def PUSH(self, operand_a, operand_b):
        # Decrement SP
        self.reg[SP] -= 1

        # Get reg_num to push
        # reg_num = self.ram_read(self.pc + 1)
        # Same as operand_a

        # Get the value to push
        value = self.reg[operand_a]

        # Copy the value to the SP address
        top_of_stack_address = self.reg[SP]
        self.ram[top_of_stack_address] = value

    def POP(self, operand_a, operand_b):
        # Get reg to pop into
        # reg_num = self.ram_read(self.pc + 1)
        # Same as operand_a

        # Get the top stack of address
        top_of_stack_address = self.reg[SP]

        # Get the value of the top of the stack
        value = self.ram[top_of_stack_address]

        # Store the value in register
        self.reg[operand_a] = value

        # Increment the SP
        self.reg[SP] += 1

    def CALL(self, operand_a, operand_b):

        self.reg[SP] -= 1

        top_of_stack_address = self.reg[SP]

        self.ram[top_of_stack_address] = self.pc + 2

        self.pc = self.reg[operand_a]


    def RET(self, operand_a, operand_b):

        top_of_stack_address = self.reg[SP]

        value = self.ram[top_of_stack_address]

        self.pc = value

        self.reg[SP] += 1

    def CMP(self,operand_a, operand_b):

        # 00000LGE
        # L Less-than: during a CMP, set to 1 if registerA is less than registerB, zero otherwise.
        # G Greater-than: during a CMP, set to 1 if registerA is greater than registerB, zero otherwise.
        # E Equal: during a CMP, set to 1 if registerA is equal to registerB, zero otherwise.

        if self.reg[operand_a] == self.reg[operand_b]:
            self.FL = 0b00000001
        elif self.reg[operand_a] < self.reg[operand_b]:
            self.FL = 0b00000100
        elif self.reg[operand_a] > self.reg[operand_b]:
            self.FL = 0b00000010

    def JMP(self, operand_a, operand_b):

        # Jump to the address stored in the given register
        # Set the PC to the address stored in the given register

        self.pc = self.reg[operand_a]

    def JEQ(self, operand_a, operand_b):

        # If equal flag is true
        # Jump to the address in the given reg

        if self.FL == 0b00000001:
            self.pc = self.reg[operand_a]
        else:
            self.pc += 2

    def JNE(self, operand_a, operand_b):
        # If equal flag is false
        # Jump to the address in the given reg
        if self.FL != 0b00000001:
            self.pc = self.reg[operand_a]
        else:
            self.pc += 2

    def run(self):
        """Run the CPU."""

        while self.running:

            ir = self.ram_read(self.pc)
            operand_a = self.ram_read(self.pc + 1)
            operand_b = self.ram_read(self.pc + 2)

            if ir in self.branch_table:
                self.branch_table[ir](operand_a, operand_b)
                ops = ir >> 6
                # check if this code will auto set the pc or not
                set_directly = (ir & 0b10000) >> 4  # mask
                if (set_directly == 0):
                    self.pc += ops + 1

            else:
                sys.exit(1)
