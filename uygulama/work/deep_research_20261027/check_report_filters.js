// Execute only the report's own filter code against inert DOM fixtures.
// No browser, network, application control, or file URL navigation is used.
const fs = require('fs');
const vm = require('vm');
const input = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const cards = input.cards.map(c => ({dataset:{priority:c.priority,domain:c.domain},textContent:c.text,hidden:false,open:false}));
const elements = Object.fromEntries(['q','priority','domain','expand','count'].map(id => ['#'+id,{value:'',textContent:'',events:{},addEventListener(event,fn){this.events[event]=fn;}}]));
const document={querySelectorAll(selector){if(selector!=='.issue')throw Error(selector);return cards;},querySelector(selector){if(!elements[selector])throw Error(selector);return elements[selector];}};
vm.runInNewContext(input.script,{document},{timeout:1000});
const checks=[];
function expect(name, expected){const count=cards.filter(c=>!c.hidden).length;if(count!==expected)throw Error(name+': '+count+' != '+expected);checks.push({name,visible:count,passed:true});}
function update(){elements['#q'].events.input();}
expect('initial_all',26);
for(const [priority,count] of Object.entries({P0:7,P1:12,P2:6,P3:1})){elements['#priority'].value=priority;update();expect('priority_'+priority,count);}
elements['#priority'].value='';elements['#domain'].value='Gerçek İHA';update();expect('project_domain',2);
elements['#priority'].value='P2';update();expect('combined_no_matches',0);
elements['#priority'].value='';elements['#domain'].value='';elements['#q'].value='İNCE AĞIN SAYISAL';update();expect('turkish_case_search',1);
elements['#expand'].events.click();if(!cards.filter(c=>!c.hidden).every(c=>c.open))throw Error('expand failed');
elements['#expand'].events.click();if(cards.filter(c=>!c.hidden).some(c=>c.open))throw Error('collapse failed');
checks.push({name:'visible_expand_collapse',passed:true});
elements['#q'].value='';update();expect('clear_filters',26);
if(cards.length!==26)throw Error('Filtering removed evidence');
console.log(JSON.stringify({checks,passed:true,scope:'Inert DOM functional check, not browser visual verification'}));
