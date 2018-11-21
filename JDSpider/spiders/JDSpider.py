#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__author__ = 'Kandy.Ye'
__mtime__ = '2017/4/12'
"""

import re
import logging
import json
import requests
from scrapy import Spider
from scrapy.selector import Selector
from scrapy.http import Request
from JDSpider.items import *


key_word = ['book', 'e', 'channel', 'mvd', 'list']
Base_url = 'https://list.jd.com'
price_url = 'https://p.3.cn/prices/mgets?skuIds=J_'
comment_url = 'https://club.jd.com/comment/productPageComments.action?productId=%s&score=0&sortType=5&page=%s&pageSize=10'
favourable_url = 'https://cd.jd.com/promotion/v2?skuId=%s&area=1_72_2799_0&shopId=%s&venderId=%s&cat=%s'


class JDSpider(Spider):
    name = "JDSpider"
    allowed_domains = ["jd.com"]
    start_urls = [
        'https://www.jd.com/allSort.aspx'
    ]
    logging.getLogger("requests").setLevel(logging.WARNING)  # 将requests的日志级别设成WARNING

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse_category)

    def parse_category(self, response):
        """获取分类页"""
        selector = Selector(response)
        try:
            texts = selector.xpath('//div[@class="category-item m"]/div[@class="mc"]/div[@class="items"]/dl/dd/a').extract()
            for text in texts:
                items = re.findall(r'<a href="(.*?)" target="_blank">(.*?)</a>', text)
                for item in items:
                    if item[0].split('.')[0][2:] in key_word:
                        if item[0].split('.')[0][2:] != 'list':
                            yield Request(url='https:' + item[0], callback=self.parse_category)
                        else:
                            categoriesItem = CategoriesItem()
                            categoriesItem['name'] = item[1]
                            categoriesItem['url'] = 'https:' + item[0]
                            categoriesItem['_id'] = item[0].split('=')[1].split('&')[0]
                            yield categoriesItem
                            yield Request(url='https:' + item[0], callback=self.parse_list)
        except Exception as e:
            print('error:', e)

        # 测试
        # yield Request(url='https://list.jd.com/list.html?cat=1315,1343,9720', callback=self.parse_list)

    def parse_list(self, response):
        """分别获得商品的地址和下一页地址"""
        meta = dict()
        meta['category'] = response.url.split('=')[1].split('&')[0]

        selector = Selector(response)
        texts = selector.xpath('//*[@id="plist"]/ul/li/div/div[@class="p-img"]/a').extract()
        for text in texts:
            items = re.findall(r'<a target="_blank" href="(.*?)">', text)
            yield Request(url='https:' + items[0], callback=self.parse_product, meta=meta)

        # 测试
        # print('2')
        # yield Request(url='https://item.jd.hk/3460655.html', callback=self.parse_product, meta=meta)

        # next page
        next_list = response.xpath('//a[@class="pn-next"]/@href').extract()
        if next_list:
            # print('next page:', Base_url + next_list[0])
            yield Request(url=Base_url + next_list[0], callback=self.parse_list)

    def parse_product(self, response):
        """商品页获取title,price,product_id"""
        category = response.meta['category']
        ids = re.findall(r"venderId:(.*?),\s.*?shopId:'(.*?)'", response.text)
        if not ids:
            ids = re.findall(r"venderId:(.*?),\s.*?shopId:(.*?),", response.text)
        vender_id = ids[0][0]
        shop_id = ids[0][1]

        # shop
        shopItem = ShopItem()
        shopItem['shopId'] = shop_id
        shopItem['venderId'] = vender_id
        shopItem['url1'] = 'http://mall.jd.com/index-%s.html' % (shop_id)
        try:
            shopItem['url2'] = 'https:' + response.xpath('//ul[@class="parameter2 p-parameter-list"]/li/a/@href').extract()[0]
        except:
            shopItem['url2'] = shopItem['url1']

        name = ''
        if shop_id == '0':
            name = '京东自营'
        else:
            try:
                name = response.xpath('//ul[@class="parameter2 p-parameter-list"]/li/a//text()').extract()[0]
            except:
                try:
                    name = response.xpath('//div[@class="name"]/a//text()').extract()[0].strip()
                except:
                    try:
                        name = response.xpath('//div[@class="shopName"]/strong/span/a//text()').extract()[0].strip()
                    except:
                        try:
                            name = response.xpath('//div[@class="seller-infor"]/a//text()').extract()[0].strip()
                        except:
                            name = u'京东自营'
        shopItem['name'] = name
        shopItem['_id'] = name
        yield shopItem

        productsItem = ProductsItem()
        productsItem['shopId'] = shop_id
        productsItem['category'] = category
        try:
            title = response.xpath('//div[@class="sku-name"]/text()').extract()[0].replace(u"\xa0", "").strip()
        except Exception as e:
            title = response.xpath('//div[@id="name"]/h1/text()').extract()[0]
        productsItem['name'] = title
        product_id = response.url.split('/')[-1][:-5]
        productsItem['_id'] = product_id
        productsItem['url'] = response.url

        # description
        desc = response.xpath('//ul[@class="parameter2 p-parameter-list"]//text()').extract()
        productsItem['description'] = ';'.join(i.strip() for i in desc)

        # price
        response = requests.get(url=price_url + product_id)
        price_json = response.json()
        productsItem['reallyPrice'] = price_json[0]['p']
        productsItem['originalPrice'] = price_json[0]['m']

        # 优惠
        res_url = favourable_url % (product_id, shop_id, vender_id, category.replace(',', '%2c'))
        # print(res_url)
        response = requests.get(res_url)
        fav_data = response.json()
        if fav_data['skuCoupon']:
            desc1 = []
            for item in fav_data['skuCoupon']:
                start_time = item['beginTime']
                end_time = item['endTime']
                time_dec = item['timeDesc']
                fav_price = item['quota']
                fav_count = item['discount']
                fav_time = item['addDays']
                desc1.append(u'有效期%s至%s,满%s减%s' % (start_time, end_time, fav_price, fav_count))
            productsItem['favourableDesc1'] = ';'.join(desc1)

        if fav_data['prom'] and fav_data['prom']['pickOneTag']:
            desc2 = []
            for item in fav_data['prom']['pickOneTag']:
                desc2.append(item['content'])
            productsItem['favourableDesc1'] = ';'.join(desc2)

        data = dict()
        data['product_id'] = product_id
        yield productsItem
        yield Request(url=comment_url % (product_id, '0'), callback=self.parse_comments, meta=data)

    def parse_comments(self, response):
        """获取商品comment"""
        try:
            data = json.loads(response.text)
        except Exception as e:
            print('get comment failed:', e)
            return None

        product_id = response.meta['product_id']

        commentSummaryItem = CommentSummaryItem()
        commentSummary = data.get('productCommentSummary')
        commentSummaryItem['goodRateShow'] = commentSummary.get('goodRateShow')
        commentSummaryItem['poorRateShow'] = commentSummary.get('poorRateShow')
        commentSummaryItem['poorCountStr'] = commentSummary.get('poorCountStr')
        commentSummaryItem['averageScore'] = commentSummary.get('averageScore')
        commentSummaryItem['generalCountStr'] = commentSummary.get('generalCountStr')
        commentSummaryItem['showCount'] = commentSummary.get('showCount')
        commentSummaryItem['showCountStr'] = commentSummary.get('showCountStr')
        commentSummaryItem['goodCount'] = commentSummary.get('goodCount')
        commentSummaryItem['generalRate'] = commentSummary.get('generalRate')
        commentSummaryItem['generalCount'] = commentSummary.get('generalCount')
        commentSummaryItem['skuId'] = commentSummary.get('skuId')
        commentSummaryItem['goodCountStr'] = commentSummary.get('goodCountStr')
        commentSummaryItem['poorRate'] = commentSummary.get('poorRate')
        commentSummaryItem['afterCount'] = commentSummary.get('afterCount')
        commentSummaryItem['goodRateStyle'] = commentSummary.get('goodRateStyle')
        commentSummaryItem['poorCount'] = commentSummary.get('poorCount')
        commentSummaryItem['skuIds'] = commentSummary.get('skuIds')
        commentSummaryItem['poorRateStyle'] = commentSummary.get('poorRateStyle')
        commentSummaryItem['generalRateStyle'] = commentSummary.get('generalRateStyle')
        commentSummaryItem['commentCountStr'] = commentSummary.get('commentCountStr')
        commentSummaryItem['commentCount'] = commentSummary.get('commentCount')
        commentSummaryItem['productId'] = commentSummary.get('productId')  # 同ProductsItem的id相同
        commentSummaryItem['_id'] = commentSummary.get('productId')
        commentSummaryItem['afterCountStr'] = commentSummary.get('afterCountStr')
        commentSummaryItem['goodRate'] = commentSummary.get('goodRate')
        commentSummaryItem['generalRateShow'] = commentSummary.get('generalRateShow')
        commentSummaryItem['jwotestProduct'] = data.get('jwotestProduct')
        commentSummaryItem['maxPage'] = data.get('maxPage')
        commentSummaryItem['score'] = data.get('score')
        commentSummaryItem['soType'] = data.get('soType')
        commentSummaryItem['imageListCount'] = data.get('imageListCount')
        yield commentSummaryItem

        for hotComment in data['hotCommentTagStatistics']:
            hotCommentTagItem = HotCommentTagItem()
            hotCommentTagItem['_id'] = hotComment.get('id')
            hotCommentTagItem['name'] = hotComment.get('name')
            hotCommentTagItem['status'] = hotComment.get('status')
            hotCommentTagItem['rid'] = hotComment.get('rid')
            hotCommentTagItem['productId'] = hotComment.get('productId')
            hotCommentTagItem['count'] = hotComment.get('count')
            hotCommentTagItem['created'] = hotComment.get('created')
            hotCommentTagItem['modified'] = hotComment.get('modified')
            hotCommentTagItem['type'] = hotComment.get('type')
            hotCommentTagItem['canBeFiltered'] = hotComment.get('canBeFiltered')
            yield hotCommentTagItem

        for comment_item in data['comments']:
            comment = CommentItem()

            comment['_id'] = comment_item.get('id')
            comment['productId'] = product_id
            comment['guid'] = comment_item.get('guid')
            comment['content'] = comment_item.get('content')
            comment['creationTime'] = comment_item.get('creationTime')
            comment['isTop'] = comment_item.get('isTop')
            comment['referenceId'] = comment_item.get('referenceId')
            comment['referenceName'] = comment_item.get('referenceName')
            comment['referenceType'] = comment_item.get('referenceType')
            comment['referenceTypeId'] = comment_item.get('referenceTypeId')
            comment['firstCategory'] = comment_item.get('firstCategory')
            comment['secondCategory'] = comment_item.get('secondCategory')
            comment['thirdCategory'] = comment_item.get('thirdCategory')
            comment['replyCount'] = comment_item.get('replyCount')
            comment['score'] = comment_item.get('score')
            comment['status'] = comment_item.get('status')
            comment['title'] = comment_item.get('title')
            comment['usefulVoteCount'] = comment_item.get('usefulVoteCount')
            comment['uselessVoteCount'] = comment_item.get('uselessVoteCount')
            comment['userImage'] = 'http://' + comment_item.get('userImage')
            comment['userImageUrl'] = 'http://' + comment_item.get('userImageUrl')
            comment['userLevelId'] = comment_item.get('userLevelId')
            comment['userProvince'] = comment_item.get('userProvince')
            comment['viewCount'] = comment_item.get('viewCount')
            comment['orderId'] = comment_item.get('orderId')
            comment['isReplyGrade'] = comment_item.get('isReplyGrade')
            comment['nickname'] = comment_item.get('nickname')
            comment['userClient'] = comment_item.get('userClient')
            comment['mergeOrderStatus'] = comment_item.get('mergeOrderStatus')
            comment['discussionId'] = comment_item.get('discussionId')
            comment['productColor'] = comment_item.get('productColor')
            comment['productSize'] = comment_item.get('productSize')
            comment['imageCount'] = comment_item.get('imageCount')
            comment['integral'] = comment_item.get('integral')
            comment['userImgFlag'] = comment_item.get('userImgFlag')
            comment['anonymousFlag'] = comment_item.get('anonymousFlag')
            comment['userLevelName'] = comment_item.get('userLevelName')
            comment['plusAvailable'] = comment_item.get('plusAvailable')
            comment['recommend'] = comment_item.get('recommend')
            comment['userLevelColor'] = comment_item.get('userLevelColor')
            comment['userClientShow'] = comment_item.get('userClientShow')
            comment['isMobile'] = comment_item.get('isMobile')
            comment['days'] = comment_item.get('days')
            comment['afterDays'] = comment_item.get('afterDays')
            yield comment

            if 'images' in comment_item:
                for image in comment_item['images']:
                    commentImageItem = CommentImageItem()
                    commentImageItem['_id'] = image.get('id')
                    commentImageItem['associateId'] = image.get('associateId')  # 和CommentItem的discussionId相同
                    commentImageItem['productId'] = image.get('productId')  # 不是ProductsItem的id，这个值为0
                    commentImageItem['imgUrl'] = 'http:' + image.get('imgUrl')
                    commentImageItem['available'] = image.get('available')
                    commentImageItem['pin'] = image.get('pin')
                    commentImageItem['dealt'] = image.get('dealt')
                    commentImageItem['imgTitle'] = image.get('imgTitle')
                    commentImageItem['isMain'] = image.get('isMain')
                    yield commentImageItem

        # next page
        max_page = int(data.get('maxPage', '1'))
        if max_page > 60:
            max_page = 60
        for i in range(1, max_page):
            url = comment_url % (product_id, str(i))
            meta = dict()
            meta['product_id'] = product_id
            yield Request(url=url, callback=self.parse_comments2, meta=meta)

    def parse_comments2(self, response):
        """获取商品comment"""
        try:
            data = json.loads(response.text)
        except Exception as e:
            print('get comment failed:', e)
            return None

        product_id = response.meta['product_id']

        commentSummaryItem = CommentSummaryItem()
        commentSummary = data.get('productCommentSummary')
        commentSummaryItem['goodRateShow'] = commentSummary.get('goodRateShow')
        commentSummaryItem['poorRateShow'] = commentSummary.get('poorRateShow')
        commentSummaryItem['poorCountStr'] = commentSummary.get('poorCountStr')
        commentSummaryItem['averageScore'] = commentSummary.get('averageScore')
        commentSummaryItem['generalCountStr'] = commentSummary.get('generalCountStr')
        commentSummaryItem['showCount'] = commentSummary.get('showCount')
        commentSummaryItem['showCountStr'] = commentSummary.get('showCountStr')
        commentSummaryItem['goodCount'] = commentSummary.get('goodCount')
        commentSummaryItem['generalRate'] = commentSummary.get('generalRate')
        commentSummaryItem['generalCount'] = commentSummary.get('generalCount')
        commentSummaryItem['skuId'] = commentSummary.get('skuId')
        commentSummaryItem['goodCountStr'] = commentSummary.get('goodCountStr')
        commentSummaryItem['poorRate'] = commentSummary.get('poorRate')
        commentSummaryItem['afterCount'] = commentSummary.get('afterCount')
        commentSummaryItem['goodRateStyle'] = commentSummary.get('goodRateStyle')
        commentSummaryItem['poorCount'] = commentSummary.get('poorCount')
        commentSummaryItem['skuIds'] = commentSummary.get('skuIds')
        commentSummaryItem['poorRateStyle'] = commentSummary.get('poorRateStyle')
        commentSummaryItem['generalRateStyle'] = commentSummary.get('generalRateStyle')
        commentSummaryItem['commentCountStr'] = commentSummary.get('commentCountStr')
        commentSummaryItem['commentCount'] = commentSummary.get('commentCount')
        commentSummaryItem['productId'] = commentSummary.get('productId')  # 同ProductsItem的id相同
        commentSummaryItem['_id'] = commentSummary.get('productId')
        commentSummaryItem['afterCountStr'] = commentSummary.get('afterCountStr')
        commentSummaryItem['goodRate'] = commentSummary.get('goodRate')
        commentSummaryItem['generalRateShow'] = commentSummary.get('generalRateShow')
        commentSummaryItem['jwotestProduct'] = data.get('jwotestProduct')
        commentSummaryItem['maxPage'] = data.get('maxPage')
        commentSummaryItem['score'] = data.get('score')
        commentSummaryItem['soType'] = data.get('soType')
        commentSummaryItem['imageListCount'] = data.get('imageListCount')
        yield commentSummaryItem

        for hotComment in data['hotCommentTagStatistics']:
            hotCommentTagItem = HotCommentTagItem()
            hotCommentTagItem['_id'] = hotComment.get('id')
            hotCommentTagItem['name'] = hotComment.get('name')
            hotCommentTagItem['status'] = hotComment.get('status')
            hotCommentTagItem['rid'] = hotComment.get('rid')
            hotCommentTagItem['productId'] = hotComment.get('productId')
            hotCommentTagItem['count'] = hotComment.get('count')
            hotCommentTagItem['created'] = hotComment.get('created')
            hotCommentTagItem['modified'] = hotComment.get('modified')
            hotCommentTagItem['type'] = hotComment.get('type')
            hotCommentTagItem['canBeFiltered'] = hotComment.get('canBeFiltered')
            yield hotCommentTagItem

        for comment_item in data['comments']:
            comment = CommentItem()
            comment['_id'] = comment_item.get('id')
            comment['productId'] = product_id
            comment['guid'] = comment_item.get('guid')
            comment['content'] = comment_item.get('content')
            comment['creationTime'] = comment_item.get('creationTime')
            comment['isTop'] = comment_item.get('isTop')
            comment['referenceId'] = comment_item.get('referenceId')
            comment['referenceName'] = comment_item.get('referenceName')
            comment['referenceType'] = comment_item.get('referenceType')
            comment['referenceTypeId'] = comment_item.get('referenceTypeId')
            comment['firstCategory'] = comment_item.get('firstCategory')
            comment['secondCategory'] = comment_item.get('secondCategory')
            comment['thirdCategory'] = comment_item.get('thirdCategory')
            comment['replyCount'] = comment_item.get('replyCount')
            comment['score'] = comment_item.get('score')
            comment['status'] = comment_item.get('status')
            comment['title'] = comment_item.get('title')
            comment['usefulVoteCount'] = comment_item.get('usefulVoteCount')
            comment['uselessVoteCount'] = comment_item.get('uselessVoteCount')
            comment['userImage'] = 'http://' + comment_item.get('userImage')
            comment['userImageUrl'] = 'http://' + comment_item.get('userImageUrl')
            comment['userLevelId'] = comment_item.get('userLevelId')
            comment['userProvince'] = comment_item.get('userProvince')
            comment['viewCount'] = comment_item.get('viewCount')
            comment['orderId'] = comment_item.get('orderId')
            comment['isReplyGrade'] = comment_item.get('isReplyGrade')
            comment['nickname'] = comment_item.get('nickname')
            comment['userClient'] = comment_item.get('userClient')
            comment['mergeOrderStatus'] = comment_item.get('mergeOrderStatus')
            comment['discussionId'] = comment_item.get('discussionId')
            comment['productColor'] = comment_item.get('productColor')
            comment['productSize'] = comment_item.get('productSize')
            comment['imageCount'] = comment_item.get('imageCount')
            comment['integral'] = comment_item.get('integral')
            comment['userImgFlag'] = comment_item.get('userImgFlag')
            comment['anonymousFlag'] = comment_item.get('anonymousFlag')
            comment['userLevelName'] = comment_item.get('userLevelName')
            comment['plusAvailable'] = comment_item.get('plusAvailable')
            comment['recommend'] = comment_item.get('recommend')
            comment['userLevelColor'] = comment_item.get('userLevelColor')
            comment['userClientShow'] = comment_item.get('userClientShow')
            comment['isMobile'] = comment_item.get('isMobile')
            comment['days'] = comment_item.get('days')
            comment['afterDays'] = comment_item.get('afterDays')
            yield comment

            if 'images' in comment_item:
                for image in comment_item['images']:
                    commentImageItem = CommentImageItem()
                    commentImageItem['_id'] = image.get('id')
                    commentImageItem['associateId'] = image.get('associateId')  # 和CommentItem的discussionId相同
                    commentImageItem['productId'] = image.get('productId')  # 不是ProductsItem的id，这个值为0
                    commentImageItem['imgUrl'] = 'http:' + image.get('imgUrl')
                    commentImageItem['available'] = image.get('available')
                    commentImageItem['pin'] = image.get('pin')
                    commentImageItem['dealt'] = image.get('dealt')
                    commentImageItem['imgTitle'] = image.get('imgTitle')
                    commentImageItem['isMain'] = image.get('isMain')
                    yield commentImageItem

