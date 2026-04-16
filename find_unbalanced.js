const fs = require('fs');
const open = fs.readFileSync('open.txt', 'utf8').trim().split('\n').map(Number);
const close = fs.readFileSync('close.txt', 'utf8').trim().split('\n').map(Number);
const content = fs.readFileSync('docs.json', 'utf8').split('\n');

let openIdx = 0;
let closeIdx = 0;
let stack = [];

while (openIdx < open.length || closeIdx < close.length) {
    if (openIdx < open.length && (closeIdx === close.length || open[openIdx] < close[closeIdx])) {
        stack.push(open[openIdx]);
        openIdx++;
    } else {
        if (stack.length === 0) {
            console.log(`Extra close bracket at line ${close[closeIdx]}`);
        } else {
            stack.pop();
        }
        closeIdx++;
    }
}
console.log('Unclosed brackets at lines:', stack);
