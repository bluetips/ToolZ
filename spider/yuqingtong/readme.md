# 金融垂直网站
## 过滤规则
1. 金融垂直网站，同关键词，不可存在相同标题文章：`check = MD5(channel+keyword+title)`
1. 关键词必须在文章或标题中


## 第一财经
1. 搜索接口无法设定时间但结果按时间排序，以此设定抓取时间
1. 搜索接口 `'https://www.yicai.com/api/ajax/getSearchResult?page={}&pagesize=20&keys={}&action=0'.format("pagenum","keyword")`
2. 返回数据格式为:
   >      {
   >      "status":1,
   >      "message":"ok",
   >      "results":{
   >          "numFound":2054,
   >          "start":0,
   >          "docs":[
   >              {
   >                  "id":"100013664",
   >                  "title":"造车新势力究竟会遇到多少坑",
   >                  "creationDate":"2018-08-20 23:08:34",
   >                  "author":"李溯婉",
   >                  "url":"/news/100013664.html",
   >                  "desc":"造车仅是0到1的过程中，就可能会遇到无数问题，例如研发能力、供应链、品质安全、资金、人才、成本以及时间等，而前面还将有更多的“坑”。",
   >                  "tags":"造车新势力;制造问题;融资问题;技术问题",
   >                  "typeo":10,
   >                  "previewImage":"https://imgcdn.yicai.com/uppics/slides/2018/08/1a5111212b4164dad33725099a542a89.jpg",
   >                  "channelid":"201",
   >                  "source":"第一财经"
   >              },
   >              {
   >                  "id":"100012936",
   >                  "title":"传华为探路彩电业，欲出手8K显示和智能大屏",
   >                  "creationDate":"2018-08-19 16:06:38",
   >                  "author":"王珍,李娜",
   >                  "url":"/news/100012936.html",
   >                  "desc":"彩电是过于成熟的品类，华为的介入可能有助于整个产业的产品梯队、价格档位、利润分配体系的重建。",
   >                  "tags":"华为;8K显示;智能家居",
   >                  "typeo":10,
   >                  "previewImage":"https://imgcdn.yicai.com/uppics/slides/2018/08/3133489703a641642b495efde1d3105b.jpg",
   >                  "channelid":"58",
   >                  "source":"第一财经"
   >              },
   >              {
   >                  "id":"100012878",
   >                  "title":"苏俊为您分享《<i>小米</i>营销智慧》",
   >                  "creationDate":"2018-08-18 22:14:03",
   >                  "url":"/video/100012878.html",
   >                  "desc":null,
   >                  "tags":"总裁读书会",
   >                  "typeo":12,
   >                  "previewImage":"http://img.mvms.yicai.com/vms-storage/9519c388c40056ea2ab0e8496425e55f41b4a7a6_2.jpg",
   >                  "channelid":"519",
   >                  "source":"VMS"
   >              },
   >              {
   >                  "id":"100012794",
   >                  "title":"趣头条拟赴美发行ADS，融资不超3亿美元",
   >                  "creationDate":"2018-08-18 12:12:46",
   >                  "author":"宁佳彦",
   >                  "url":"/news/100012794.html",
   >                  "desc":"此前被问及是否要上市时，趣头条首席运营官陈思晖就曾表示公司不会拒绝考虑任何可能的融资方式。",
   >                  "tags":"ADS;融资;趣头条",
   >                  "typeo":10,
   >                  "previewImage":"https://imgcdn.yicai.com/uppics/slides/2018/08/e7ede2ae3e55bc0b0bbf1fedaf8ebb43.jpg",
   >                  "channelid":"58",
   >                  "source":"第一财经"
   >              },
   >              {
   >                  "id":"100012364",
   >                  "title":"扫地机器人市场空间巨大，各品牌竞相争夺市场 ",
   >                  "creationDate":"2018-08-17 11:59:17",
   >                  "author":"王世峰",
   >                  "url":"/news/100012364.html",
   >                  "desc":"<i>小米</i>，科沃斯纷纷切入扫地机器人领域之后，曾经代表智能家居未来发展方向的扫地机器人市场竞争渐趋激烈。",
   >                  "tags":"世界机器人大会;iRobot;扫地机器人;机器人思维",
   >                  "typeo":10,
   >                  "previewImage":"https://imgcdn.yicai.com/uppics/slides/2018/08/d93b490953ec07622cbf799f76392a8c.jpg",
   >                  "channelid":"57",
   >                  "source":"第一财经"
   >              },
   >              {
   >                  "id":"100012102",
   >                  "title":"谁是汽车圈的苹果？丨推本溯源",
   >                  "creationDate":"2018-08-16 20:45:14",
   >                  "author":"李溯婉",
   >                  "url":"/news/100012102.html",
   >                  "desc":"未来存在诸多可能性，有人认为，造车新势力中将会有两三家突围，将成为汽车圈的苹果、华为和<i>小米</i>，但也有人悲观认为，现有的造车新势力将可能全军覆没，无一幸存。",
   >                  "tags":"造车;苹果;蔚来;小鹏",
   >                  "typeo":10,
   >                  "previewImage":"https://imgcdn.yicai.com/uppics/slides/2018/08/f59f388360a301efc06e1c8cbd4951fa.jpg",
   >                  "channelid":"201",
   >                  "source":"第一财经APP"
   >              },
   >              {
   >                  "id":"100011902",
   >                  "title":"腾讯的糖，没吃上；腾讯的锅，全背了！中概科技股暴跌",
   >                  "creationDate":"2018-08-16 15:56:35",
   >                  "author":"张苑柯",
   >                  "url":"/news/100011902.html",
   >                  "desc":"腾讯公司公布了2018年第二季度业绩和2018年上半年业绩低于市场预期，中概股科技股进一步呈现下跌态势。",
   >                  "tags":"腾讯;中概股;科技股;美股;恒生指数",
   >                  "typeo":10,
   >                  "previewImage":"https://imgcdn.yicai.com/uppics/slides/2018/08/aadc2b2c372fad291f995b23bdf305c9.jpg",
   >                  "channelid":"54",
   >                  "source":"第一财经APP"
   >              },
   >              {
   >                  "id":"100011575",
   >                  "title":"业绩不佳又逢外部环境动荡，两地科技股纷纷跌下神坛",
   >                  "creationDate":"2018-08-15 21:59:24",
   >                  "author":"蒋琰",
   >                  "url":"/news/100011575.html",
   >                  "desc":"两地科技股走低，市场人士认为有外部环境因素也有个股业绩不佳带累大盘的原因。",
   >                  "tags":"科技股;创业板;港股;腾讯",
   >                  "typeo":10,
   >                  "previewImage":"https://imgcdn.yicai.com/uppics/slides/2018/08/2f3c87e4cba9ebaeb96b97c0e98acc1c.jpg",
   >                  "channelid":"54",
   >                  "source":"第一财经APP"
   >              },
   >              {
   >                  "id":"100011389",
   >                  "title":"美团VS饿了么，远远不止外卖",
   >                  "creationDate":"2018-08-15 17:06:05",
   >                  "url":"/news/100011389.html",
   >                  "desc":"近日，正值饿了么十周年，于今年4月投入阿里怀抱的饿了么充分享用了阿里的资金和资源，推出一系列活动加快业务拓张和市场占领。事实上，美团与饿了么的竞争虽缘起外卖，战火却早已蔓延到更加广阔的本地服务业务上。",
   >                  "tags":"美团;饿了么;阿里巴巴;外卖;本地服务",
   >                  "typeo":10,
   >                  "previewImage":"https://imgcdn.yicai.com/uppics/slides/2018/08/3dee140040531c3e03fd4f3970143124.jpg",
   >                  "channelid":"453",
   >                  "source":"第一财经"
   >              },
   >              {
   >                  "id":"100010673",
   >                  "title":"<i>小米</i>生态链落户松江 关注<i>小米</i>产业链投资机会",
   >                  "creationDate":"2018-08-14 15:12:39",
   >                  "url":"/video/100010673.html",
   >                  "desc":null,
   >                  "tags":"小米 松江 投资",
   >                  "typeo":12,
   >                  "previewImage":"http://img.mvms.yicai.com/vms-storage/sources/fb/5b727bd8d3763_3.jpg",
   >                  "channelid":"448",
   >                  "source":"VMS"
   >              },
   >              {
   >                  "id":"100010452",
   >                  "title":"<i>小米</i>生态链落户松江，关注<i>小米</i>产业链投资机会",
   >                  "creationDate":"2018-08-14 08:37:40",
   >                  "url":"/news/100010452.html",
   >                  "desc":"除<i>小米</i>自身投资价值之外，投资者也应当关注<i>小米</i>生态带动的产业链投资机会",
   >                  "tags":"小米;生态;松江;产业链;供应链管理",
   >                  "typeo":10,
   >                  "previewImage":"https://imgcdn.yicai.com/uppics/slides/2018/08/4f0f46b0c1c4096d65c8bac0d832e23c.jpg",
   >                  "channelid":"54",
   >                  "source":"第一财经"
   >              },
   >              {
   >                  "id":"100010368",
   >                  "title":"5G大潮美国占先机？中国胜在规模，华为还拒收高额专利费",
   >                  "creationDate":"2018-08-13 22:57:09",
   >                  "author":"钱童心",
   >                  "url":"/news/100010368.html",
   >                  "desc":"中国目前支持5G通信的基站是美国的10倍多。",
   >                  "tags":"5G;中国铁塔;华为;高通;移动通信",
   >                  "typeo":10,
   >                  "previewImage":"https://imgcdn.yicai.com/uppics/slides/2018/08/1ebae74c9509e3fc057595e17975885a.jpg",
   >                  "channelid":"58",
   >                  "source":"第一财经APP"
   >              },
   >              {
   >                  "id":"100010300",
   >                  "title":"马斯克：怀揣梦想的科技狂人 | 人物",
   >                  "creationDate":"2018-08-13 21:18:22",
   >                  "author":"钱童心",
   >                  "url":"/news/100010300.html",
   >                  "desc":"马斯克认为，生活不能仅仅是解决一个又一个悲惨的问题，我们需要一些鼓励，让你每天醒来时都乐意作为人类的一分子。",
   >                  "tags":"梦想;火星;科技;特斯拉",
   >                  "typeo":10,
   >                  "previewImage":"https://imgcdn.yicai.com/uppics/slides/2018/08/cb9a84f1cac2383ab1278725d99a9509.jpg",
   >                  "channelid":"57",
   >                  "source":"第一财经APP"
   >              },
   >              {
   >                  "id":"100010284",
   >                  "title":"国产OLED手机屏下半年进入突破期丨如数家珍",
   >                  "creationDate":"2018-08-13 20:55:27",
   >                  "author":"王珍",
   >                  "url":"/news/100010284.html",
   >                  "desc":"中国OLED手机屏将在今年下半年进入关键的突破期。",
   >                  "tags":"OLED;下半年;国产;智能手机",
   >                  "typeo":10,
   >                  "previewImage":"https://imgcdn.yicai.com/uppics/slides/2018/08/cf9f71a6ce00770e4437cbb03976aa4a.jpg",
   >                  "channelid":"58",
   >                  "source":"第一财经APP"
   >              },
   >              {
   >                  "id":"100010183",
   >                  "title":"市场份额暴跌，三星的中国“失误”",
   >                  "creationDate":"2018-08-13 18:49:23",
   >                  "author":"李娜",
   >                  "url":"/news/100010183.html",
   >                  "desc":"三星在中国市场的下滑主要是策略的失误，过早的削减中低端产品线以及产品开发失误，都给国产手机厂商带来了赶超的机会。",
   >                  "tags":"三星;中国市场份额1%;国产手机追赶;工厂承压",
   >                  "typeo":10,
   >                  "previewImage":"https://imgcdn.yicai.com/uppics/slides/2018/08/a4cd7be5650715b3dbeb33df0a89bf96.jpg",
   >                  "channelid":"58",
   >                  "source":"第一财经APP"
   >              },
   >              {
   >                  "id":"100009750",
   >                  "title":"渠道变奏，OPPO在华强北开出“超级旗舰店”",
   >                  "creationDate":"2018-08-12 19:07:13",
   >                  "author":"李娜",
   >                  "url":"/news/100009750.html",
   >                  "desc":"在经历了最好的时机和最残酷的洗礼后，山寨文化“褪下”昔日的荣光，华强北正式进入升级改造，OPPO则进入国产四强共同抢下七成市场，中小品牌逐渐消失。",
   >                  "tags":"OPPO;渠道改革;超级旗舰店;头部企业强者之争",
   >                  "typeo":10,
   >                  "previewImage":"https://imgcdn.yicai.com/uppics/slides/2018/08/1374ffe8e9d9152ff0391c193b7fc2b8.jpg",
   >                  "channelid":"58",
   >                  "source":"第一财经APP"
   >              },
   >              {
   >                  "id":"100009553",
   >                  "title":"韩冰：新零售模式 打造特定性价比丨投资人说",
   >                  "creationDate":"2018-08-11 10:25:27",
   >                  "author":"张婧雯",
   >                  "url":"/news/100009553.html",
   >                  "desc":null,
   >                  "tags":"韩冰;新零售;小米;投资人说",
   >                  "typeo":10,
   >                  "previewImage":"https://imgcdn.yicai.com/uppics/slides/2018/08/74cd3eefc87cf20c18d64e21415cb88b.jpg",
   >                  "channelid":"451",
   >                  "source":"第一财经"
   >              },
   >              {
   >                  "id":"100009391",
   >                  "title":"一周全球新闻瞬间精选（08.04-08.10）",
   >                  "creationDate":"2018-08-10 19:20:03",
   >                  "author":"新华网 视觉中国 东方IC",
   >                  "url":"/image/100009391.html",
   >                  "desc":"一周全球新闻瞬间精选（08.04-08.10）",
   >                  "tags":"一周全球新闻瞬间精选（08.04-08.10）",
   >                  "typeo":11,
   >                  "previewImage":"https://imgcdn.yicai.com/uppics/slides/2018/08/97cb6d10ee95d5d07caa1c8aeb32f293.jpg",
   >                  "channelid":"461",
   >                  "source":"第一财经"
   >              },
   >              {
   >                  "id":"100009048",
   >                  "title":"韩冰：看好<i>小米</i> 未来整体营收会超预期",
   >                  "creationDate":"2018-08-10 08:59:52",
   >                  "url":"/video/100009048.html",
   >                  "desc":null,
   >                  "tags":"韩冰 小米",
   >                  "typeo":12,
   >                  "previewImage":"http://img.mvms.yicai.com/vms-storage/sources/fb/5b6ccfa09e456_1.jpg",
   >                  "channelid":"448",
   >                  "source":"VMS"
   >              },
   >              {
   >                  "id":"100008860",
   >                  "title":"中报眼|拆解欧菲科技中报，苹果概念龙头大跌另有隐情",
   >                  "creationDate":"2018-08-09 19:15:10",
   >                  "author":"双名",
   >                  "url":"/news/100008860.html",
   >                  "desc":"“欧菲科技，有他的问题。”国内某中型基金公司基金经理对第一财经称，一季度业绩增长50%多，二季度增长20%，，处于市场的预期范围内，超预期可能谈不上。",
   >                  "tags":"中报;欧菲科技;苹果产业链;财务问题;去杠杆",
   >                  "typeo":10,
   >                  "previewImage":"https://imgcdn.yicai.com/uppics/slides/2018/08/0e54e1305c2958a084332b8d6fa7542b.jpg",
   >                  "channelid":"54",
   >                  "source":"第一财经APP"
   >              }
   >          ]
   >      }
   >      }

1. 文章内容 xpath `//div[@class="m-txt"]/p//text()`,图文文章xpath `//ul[@class="ad-thumb-list"]/li/a/img/@data-ad-desc`,视频类型文章不抓取

## 新浪财经
1. 搜索接口   `url = 'http://search.sina.com.cn/?c=news&q=%s&range=all&time=custom&stime=%s&etime=%s&num=10&page=%s'%(keyword,startime,endtime,pn)`
2. 单条记录xpath    `//div[contains(@class,"r-info r-info2")]`
3. 文章内容     `//div[@id="artibody"]//p/text()`


##  财联社

1.   搜索接口 `'https://www.cailianpress.com/api/search/get_all_list?type=%s&keyword=%s&page=%s&rn=20'%(Types,keyword,pn)`

      >     if Types=='telegram':电报文章
      >     if Types=='depth':深度文章
