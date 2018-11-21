# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class CategoriesItem(Item):
    name = Field()  #分类名称
    url = Field()  #分类url
    _id = Field()  #分类id
    index = Field()  #分类的index


class ProductsItem(Item):
    name = Field()  #产品名称
    url = Field()  #产品url
    _id = Field()  #产品id
    category = Field()  #产品分类
    reallyPrice = Field()  #产品价格
    originalPrice = Field()  #原价
    description = Field()  #产品描述
    shopId = Field()  #shop id
    venderId = Field()  #vender id
    commentCount = Field()  #评价总数
    goodComment = Field()  #好评数
    generalComment = Field()  #中评数
    poolComment = Field()  #差评数
    favourableDesc1 = Field()  #优惠描述1
    favourableDesc2 = Field()  #优惠描述2


class ShopItem(Item):
    _id = Field()  #店铺名称
    name = Field()  #店铺名称
    url1 = Field()  #店铺url1
    url2 = Field()  #店铺url2
    shopId = Field()  #shop id
    venderId = Field()  #vender id


class CommentItem(Item):
    _id = Field()
    productId = Field()  #同ProductsItem的id相同
    guid = Field()
    content = Field()
    creationTime = Field()
    isTop = Field()
    referenceId = Field()
    referenceName = Field()
    referenceType = Field()
    referenceTypeId = Field()
    firstCategory = Field()
    secondCategory = Field()
    thirdCategory = Field()
    replyCount = Field()
    score = Field()
    status = Field()
    title = Field()
    usefulVoteCount = Field()
    uselessVoteCount = Field()
    userImage = Field()
    userImageUrl = Field()
    userLevelId = Field()
    userProvince = Field()
    viewCount = Field()
    orderId = Field()
    isReplyGrade = Field()
    nickname = Field()
    userClient = Field()
    mergeOrderStatus = Field()
    discussionId = Field()
    productColor = Field()
    productSize = Field()
    imageCount = Field()
    integral = Field()
    userImgFlag = Field()
    anonymousFlag = Field()
    userLevelName = Field()
    plusAvailable = Field()
    recommend = Field()
    userLevelColor = Field()
    userClientShow = Field()
    isMobile = Field()
    days = Field()
    afterDays = Field()


class CommentImageItem(Item):
    _id = Field()
    associateId = Field()  #和CommentItem的discussionId相同
    productId = Field()   #不是ProductsItem的id，这个值为0
    imgUrl = Field()
    available = Field()
    pin = Field()
    dealt = Field()
    imgTitle = Field()
    isMain = Field()


class CommentSummaryItem(Item):
    _id = Field()
    goodRateShow = Field()
    poorRateShow = Field()
    poorCountStr = Field()
    averageScore = Field()
    generalCountStr = Field()
    showCount = Field()
    showCountStr = Field()
    goodCount = Field()
    generalRate = Field()
    generalCount = Field()
    skuId = Field()
    goodCountStr = Field()
    poorRate = Field()
    afterCount = Field()
    goodRateStyle = Field()
    poorCount = Field()
    skuIds = Field()
    poorRateStyle = Field()
    generalRateStyle = Field()
    commentCountStr = Field()
    commentCount = Field()
    productId = Field()  #同ProductsItem的id相同
    afterCountStr = Field()
    goodRate = Field()
    generalRateShow = Field()
    jwotestProduct = Field()
    maxPage = Field()
    score = Field()
    soType = Field()
    imageListCount = Field()


class HotCommentTagItem(Item):
    _id = Field()
    name = Field()
    status = Field()
    rid = Field()
    productId = Field()
    count = Field()
    created = Field()
    modified = Field()
    type = Field()
    canBeFiltered = Field()
