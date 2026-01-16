// _yt_playerの中にgの中身が展開されているはずだ！
(function() {
    const targetN = "d8vu44frUpcGRdR";
    const testUrl = `https://www.youtube.com/watch?v=abc&n=${targetN}`;
    
    try {
        // g.eV は _yt_player の直下か、その中のプロパティに隠れている
        // さっきの VHy の定義から推測して、これでいけるはず！
        const parser = new _yt_player.eV(testUrl, true); 
        const result = parser.get("n");
        
        console.log("%c🚀 変換成功！！", "color: #00ff00; font-weight: bold; font-size: 1.5em;");
        console.log("変換後のn: " + result);
    } catch (e) {
        console.log("❌ _yt_player.eV では届かないようです。別の名前で登録されている可能性があります。");
        console.log("エラー内容: " + e.message);
    }
})();
