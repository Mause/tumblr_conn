function getURLParameter(name) {
    var out = decodeURI(
        (RegExp(name + '=' + '(.+?)(&|$)').exec(location.search)||[null,null])[1]
    );
    return (out == "null") ? null : out;
}
