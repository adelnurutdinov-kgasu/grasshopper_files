import ghparse
from ghparse import it,items,chs,ch
def objects(root):
    d=ch(root,'Definition'); o=ch(d,'DefinitionObjects')
    return d,chs(o,'Object')
def build(root):
    d,obs=objects(root)
    L=[];owner={};pinfo={}
    for idx,ob in enumerate(obs):
        cont=ch(ob,'Container'); a=ch(cont,'Attributes')
        e={'i':idx,'type':it(ob,'Name'),'guid':it(cont,'InstanceGuid'),'nick':it(cont,'NickName'),
           'pivot':it(a,'Pivot'),'bounds':it(a,'Bounds'),'cont':cont,'srcs':[], 'ob':ob}
        owner[e['guid']]=idx
        def walk(c,top):
            g=it(c,'InstanceGuid')
            if g and not top:
                owner[g]=idx; pinfo[g]=(idx,it(c,'NickName') or it(c,'Name'),c['n'])
            for i,v in items(c,'Source'):
                e['srcs'].append((it(c,'NickName') or it(c,'Name'),v))
            for x in c['ch']:
                if x['n'] not in ('ClusterDocument',): walk(x,False)
        walk(cont,True)
        L.append(e)
    edges=[]
    for e in L:
        for pn,s in e['srcs']:
            if s in owner: edges.append((owner[s],e['i'],pinfo.get(s,(None,'',''))[1],pn))
            else: edges.append((None,e['i'],'?',pn))
    return d,L,edges,owner,pinfo
