let i=0;
function RPCcall(method, params, callback){
    i++;
    let obj = {"jsonrpc": "2.0", "method": method, "params": params, "id": i};

    let xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function(){
        if ( this.readyState == 4 && this.status == 200){
            callback(this.responseText);
        }    
    };
    xhttp.open("POST", "/rpc", true);
    xhttp.send(JSON.stringify(obj));
}
