const fs = require('fs');
const content = fs.readFileSync('/Volumes/SSK SSD/Projects/mintlify-docs/docs.json', 'utf8');
let stack = [];
for (let i = 0; i < content.length; i++) {
    const char = content[i];
    if (char === '{' || char === '[') {
        stack.push({char, pos: i, line: content.slice(0, i).split('\n').length});
    } else if (char === '}' || char === ']') {
        const last = stack.pop();
        if ((char === '}' && last.char !== '{') || (char === ']' && last.char !== '[')) {
            console.log(`Mismatch at line ${content.slice(0, i).split('\n').length}: expected match for ${last.char} from line ${last.line}, but found ${char}`);
            process.exit(1);
        }
    }
}
if (stack.length > 0) {
    console.log('Unclosed brackets:');
    stack.forEach(s => console.log(`${s.char} at line ${s.line}`));
} else {
    console.log('All brackets balanced');
}
