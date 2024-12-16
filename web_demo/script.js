class Assembler {
  constructor() {
      this.cpu_instructions = {
          'NOP': 0x00,
          'LDA': 0x01,
          'ADD': 0x02,
          'SUB': 0x03,
          'STA': 0x04,
          'JMP': 0x05,
          'JZ': 0x06,
          'HALT': 0xFF
      };
      
      this.gpu_instructions = {
          'GNOP': 0x00,
          'SETX': 0x01,
          'SETY': 0x02,
          'SETC': 0x03,
          'PLOT': 0x04,
          'CLEAR': 0x05,
          'LINE': 0x06,
          'RECT': 0x07,
          'GHALT': 0xFF
      };
      
      this.symbols = {};
  }

  isNumber(s) {
      if (s.startsWith('0x')) {
          return !isNaN(parseInt(s, 16));
      } else if (s.startsWith('0b')) {
          return !isNaN(parseInt(s.slice(2), 2));
      }
      return !isNaN(parseInt(s));
  }

  parseValue(s) {
      if (s.startsWith('0x')) {
          return parseInt(s, 16);
      } else if (s.startsWith('0b')) {
          return parseInt(s.slice(2), 2);
      }
      return parseInt(s);
  }

  assemble(source) {
      const lines = source.split('\n');
      const cleaned_lines = [];
      let current_address = 0;
      let mode = 'CPU';

      for (let line of lines) {
          line = line.split(';')[0].trim();
          if (!line) continue;

          if (line.startsWith('.')) {
              const directive = line.slice(1).toUpperCase();
              if (['CPU', 'GPU'].includes(directive)) {
                  mode = directive;
                  cleaned_lines.push([mode, line]);
                  continue;
              } else {
                  throw new Error(`Unknown directive: ${line}`);
              }
          }

          if (line.includes(':')) {
              const [label, rest] = line.split(':');
              this.symbols[label.trim()] = current_address;
              line = rest.trim();
              if (!line) continue;
          }
          
          cleaned_lines.push([mode, line]);
          const parts = line.split(/\s+/);
          current_address += 1;
          if (parts.length > 1) {
              current_address += parts.length - 1;
          }
      }

      const machine_code = [];
      mode = 'CPU';
      
      for (const [stored_mode, line] of cleaned_lines) {
          if (line.startsWith('.')) {
              mode = stored_mode;
              continue;
          }
          
          const parts = line.split(/\s+/);
          const instruction = parts[0].toUpperCase();
          
          const instruction_set = mode === 'CPU' ? this.cpu_instructions : this.gpu_instructions;
          
          if (!(instruction in instruction_set)) {
              throw new Error(`Unknown ${mode} instruction: ${instruction}`);
          }
          
          machine_code.push(instruction_set[instruction]);

          if (parts.length > 1) {
              for (const operand of parts.slice(1)) {
                  if (this.isNumber(operand)) {
                      const value = this.parseValue(operand);
                      if (value > 255) {
                          throw new Error(`Operand value too large: ${operand}`);
                      }
                      machine_code.push(value);
                  } else if (operand in this.symbols) {
                      machine_code.push(this.symbols[operand]);
                  } else {
                      throw new Error(`Unknown operand: ${operand}`);
                  }
              }
          }
      }
      
      return machine_code;
  }
}

class Compiler {
  constructor() {
      this.variables = {};
      this.current_section = "CPU";
      this.output = [];
  }
  
  compile(source) {
      const lines = source.split('\n');
      this.output = [];
      
      for (const line of lines) {
          const trimmedLine = line.trim();
          
          if (trimmedLine === 'compute') {
              this.output.push('.CPU');
              this.current_section = 'CPU';
          } else if (trimmedLine === 'draw') {
              this.output.push('.GPU');
              this.current_section = 'GPU';
          } else if (trimmedLine.startsWith('var')) {
              const parts = trimmedLine.split('=');
              const varName = parts[0].replace('var', '').trim();
              const value = parts[1].trim();
              this.output.push(`LDA ${value}`);
              this.output.push(`STA ${(Object.keys(this.variables).length + 0x20).toString(16)}`);
              this.variables[varName] = value;
          } else if (trimmedLine.startsWith('setpos')) {
              const [_, x, y] = trimmedLine.split(' ');
              this.output.push(`SETX ${x}`);
              this.output.push(`SETY ${y}`);
          } else if (trimmedLine === 'clear') {
              this.output.push('CLEAR');
          } else if (trimmedLine.startsWith('setcolor')) {
              const [_, color] = trimmedLine.split(' ');
              this.output.push(`SETC ${color}`);
          } else if (trimmedLine.startsWith('rect')) {
              const [_, width, height] = trimmedLine.split(' ');
              this.output.push(`RECT ${width} ${height}`);
          }
      }
      
      if (this.current_section === "CPU") {
          this.output.push("HALT");
      } else {
          this.output.push("GHALT");
      }
      
      return this.output.join('\n');
  }
}

const compiler = new Compiler();

function switchTab(tabName) {
  document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
  
  const selectedTab = document.querySelector(`.tab:nth-child(${tabName === 'machineCode' ? '1' : '2'})`);
  const selectedContent = document.getElementById(`${tabName}Tab`);
  
  selectedTab.classList.add('active');
  selectedContent.classList.add('active');
}

document.getElementById('themeSwitch').addEventListener('change', function(e) {
  document.documentElement.setAttribute('data-theme', e.target.checked ? 'dark' : 'light');
});

function updateAssembly() {
  const sourceCode = document.getElementById('sourceCode').value;
  try {
      const assembly = compiler.compile(sourceCode);
      document.getElementById('assemblyOutput').value = assembly;

      const assembler = new Assembler();
      const machineCode = assembler.assemble(assembly);

      const machineCodeHex = machineCode.map(num => '0x' + num.toString(16).padStart(2, '0')).join(' ');
      document.getElementById('machineCode').textContent = machineCodeHex;

      let hexView = '';
      for (let i = 0; i < machineCode.length; i += 8) {
          const chunk = machineCode.slice(i, i + 8);
          const offset = i.toString(16).padStart(4, '0');
          const hex = chunk.map(num => num.toString(16).padStart(2, '0')).join(' ');
          const ascii = chunk.map(num => (num >= 32 && num <= 126) ? String.fromCharCode(num) : '.').join('');
          hexView += `${offset}  ${hex.padEnd(24)}  |${ascii}|\n`;
      }
      document.getElementById('hexView').textContent = hexView;
  } catch (error) {
      document.getElementById('assemblyOutput').value = `Error: ${error.message}`;
      document.getElementById('machineCode').innerHTML = `<span class="error">Error during compilation</span>`;
      document.getElementById('hexView').innerHTML = `<span class="error">Error during compilation</span>`;
  }
}

document.getElementById('sourceCode').addEventListener('input', updateAssembly);

updateAssembly();