export class Element{
 children=[];textContent='';value='';disabled=false;listeners={};attributes={};
 constructor(tag){this.tagName=tag;}
 append(...items){for(const item of items){item.parent=this;this.children.push(item);}}
 replaceChildren(...items){this.children=[];this.textContent='';this.append(...items);}
 setAttribute(k,v){this.attributes[k]=v;}
 getAttribute(k){return this.attributes[k];}
 get isConnected(){return this.root===true||Boolean(this.parent?.isConnected);}
 addEventListener(type,fn){(this.listeners[type]??=[]).push(fn);}
 querySelectorAll(selector){return elements(this).slice(1).filter(e=>selector.split(',').includes(e.tagName));}
 async dispatch(type){await Promise.all((this.listeners[type]??[]).map(fn=>fn({preventDefault(){},target:this})));}
 remove(){this.parent.children=this.parent.children.filter(x=>x!==this);}
 click(){return this.dispatch('click');}
}
export const elements=e=>[e,...e.children.flatMap(elements)];
export const text=e=>[e.textContent,...e.children.map(text)].join(' ');
export function setup(storage){
 globalThis.document={createElement:tag=>new Element(tag)};
 globalThis.localStorage=storage;
 Object.defineProperty(globalThis,'navigator',{configurable:true,value:{locks:{request:async(name,options,fn)=>fn({name})}}});
 globalThis.addEventListener=()=>{};
 const host=new Element('div');host.root=true;return host;
}
export const find=(host,tag,content)=>elements(host).find(e=>e.tagName===tag&&e.textContent.includes(content));
export const tick=()=>new Promise(resolve=>setTimeout(resolve,0));
