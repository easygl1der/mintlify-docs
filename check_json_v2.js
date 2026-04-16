const fs = require('fs');
const content = fs.readFileSync('/Volumes/SSK SSD/Projects/mintlify-docs/docs.json', 'utf8');
let stack = [];
let lines = content.split('\n');
for (let lineNo = 0; lineNo < lines.length; lineNo++) {
    let line = lines[lineNo];
    for (let char of line) {
        if (char === '{' || char === '[') {
            stack.push({char, line: lineNo + 1});
        } else if (char === '}' || char === ']') {
            if (stack.length === 0) {
                console.log(`Extra closing ${char} at line ${lineNo + 1}`);
                continue;
            }
            const last = stack.pop();
            if ((char === '}' && last.char !== '{') || (char === ']' && last.char !== '[')) {
                console.log(`Mismatch at line ${lineNo + 1}: found ${char}, but last opened was ${last.char} at line ${last.line}`);
            }
        }
    }
}
stack.forEach(s => console.log(`Unclosed ${s.char} at line ${s.line}`));
