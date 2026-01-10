debug=False
def printdebug(ss):
    if debug:
        print ss
def getval(strval):
    strval=strval.strip()
    if 'slice' in strval:
        strval=strval.split(".slice(")#.replace(',',':')+']'
        strval=strval[0]+"["+strval[1].split(')')[0].replace(',',':')+"]"
    elif 'String.fromCharCode' in strval:
        strval=strval.replace('String.fromCharCode','chr')
    elif 'charAt' in strval:
        strval=strval.replace('.charAt','[').replace('(','').replace(')','')+']'
    if 'substr' in strval:
        strval=strval.split(".substr(")#.replace(',',':')+']'
        f,t=strval[1].split(')')[0].split(',')
        
        strval=strval[0]+"["+f+":"+f+'+'+t +"]"
        printdebug( strval)
    return eval(strval)
def getSecuriCookie(html):
    import re
    puts=re.findall("S='(.*?)';",html)[0]
    puts= puts.decode("base64")
    printdebug( puts)
    val=re.findall("[a-z]=([\"'].*?);",puts,re.DOTALL)[0]
    vals=re.findall('(.*?)[ ]?\+',val)
    v=""
    for vv in vals:
        v+=getval(vv)
    e=v
    val=re.findall("cookie=(.*?);",puts,re.DOTALL)[0]
    vals=re.findall('(.*?)[ ]?\+',val)
    printdebug( vals)
    c=""
    for vv in vals:
        c+=getval(vv)
    c+=v
    return c
#print getSecuriCookie("<html><title>You are being redirected...</title><noscript>Javascript is required. Please enable javascript before you are allowed to see this page.</noscript><script>var s={},u,c,U,r,i,l=0,a,e=eval,w=String.fromCharCode,sucuri_cloudproxy_js='',S='cD0iOSIuc2xpY2UoMCwxKSArIFN0cmluZy5mcm9tQ2hhckNvZGUoNTEpICsgIjkiLnNsaWNlKDAsMSkgKyAnTDUnLnNsaWNlKDEsMikrIjBzdSIuc2xpY2UoMCwxKSArICAnJyArIjlzdWN1ciIuY2hhckF0KDApKyJlIiArICIiICsiOSIgKyAgJycgKyJlIi5zbGljZSgwLDEpICsgICcnICsiMXN1Ii5zbGljZSgwLDEpICsgJz8zJy5zbGljZSgxLDIpKyAnJyArJycrJ3hPZCcuY2hhckF0KDIpKyJkc3UiLnNsaWNlKDAsMSkgKyBTdHJpbmcuZnJvbUNoYXJDb2RlKDU3KSArICIiICsnMXM0YScuc3Vic3RyKDMsIDEpICsnMScgKyAgU3RyaW5nLmZyb21DaGFyQ29kZSg1MCkgKyAnNGhaNycuc3Vic3RyKDMsIDEpICsnNScgKyAgICcnICsgCiJkIiArIFN0cmluZy5mcm9tQ2hhckNvZGUoMHg2MSkgKyBTdHJpbmcuZnJvbUNoYXJDb2RlKDU2KSArICIiICsnUmZXYicuc3Vic3RyKDMsIDEpICsgJycgKyAKJzYnICsgICAnJyArU3RyaW5nLmZyb21DaGFyQ29kZSgweDYzKSArICc+NCcuc2xpY2UoMSwyKSsnRXVPMicuc3Vic3RyKDMsIDEpICsgJycgKyJlIiArICIyc3UiLnNsaWNlKDAsMSkgKyAiNnN1Ii5zbGljZSgwLDEpICsgIiIgKydyWzcnLmNoYXJBdCgyKSsnRmw4ZScuc3Vic3RyKDMsIDEpICsgJycgKycnO2RvY3VtZW50LmNvb2tpZT0ncycrJ3UnKydjcycuY2hhckF0KDApKyd1JysncicrJ2lzJy5jaGFyQXQoMCkrJ18nKycnKydjJysnbHN1Jy5jaGFyQXQoMCkgKydvJysnc3VjdXJ1Jy5jaGFyQXQoNSkgKyAnZCcrJ3BzdWN1cmknLmNoYXJBdCgwKSArICdyJysnbycrJ3gnKyd5JysnX3N1Y3UnLmNoYXJBdCgwKSAgKyd1JysnJysndScrJ2lzJy5jaGFyQXQoMCkrJ2QnKydfJysnc3VhJy5jaGFyQXQoMikrJzEnKycnKydzdWN1cmlhJy5jaGFyQXQoNikrJzNzdWN1cmknLmNoYXJBdCgwKSArICdic3VjdScuY2hhckF0KDApICArJzQnKycnKycyJysnJysnOCcrJ2RzdScuY2hhckF0KDApICsiPSIgKyBwOyBsb2NhdGlvbi5yZWxvYWQoKTs=';L=S.length;U=0;r='';var A='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';for(u=0;u<64;u++){s[A.charAt(u)]=u;}for(i=0;i<L;i++){c=s[S.charAt(i)];U=(U<<6)+c;l+=6;while(l>=8){((a=(U>>>(l-=8))&0xff)||(i<(L-2)))&&(r+=w(a));}}e(r);</script></html>")
