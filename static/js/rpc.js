let i=0;
function RPCcall(method, params, user_id, session, callback){
    i++;
    if (user_id == null && session == null) {
        var obj = {"jsonrpc": "2.0", "method": method, "params": params, "id": i};
    }
    else {
        var obj = {"jsonrpc": "2.0", "method": method, "params": params, "user_id" : user_id, "session" : session, "id": i};
	}
    
    let xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function(){
        if ( this.readyState == 4 && this.status == 200){
            callback(this.responseText);
        }    
    };
    xhttp.open("POST", "/rpc", true);
    xhttp.send(JSON.stringify(obj));
}