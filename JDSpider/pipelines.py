# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
from JDSpider.items import *


class MongoDBPipeline(object):
    def __init__(self):
        clinet = pymongo.MongoClient("localhost", 27017)
        db = clinet["JD"]
        self.Categories = db["Categories"]
        self.Products = db["Products"]
        self.Shop = db["Shop"]
        self.Comment = db["Comment"]
        self.CommentImage = db["CommentImage"]
        self.CommentSummary = db["CommentSummary"]
        self.HotCommentTag = db["HotCommentTag"]

    def process_item(self, item, spider):
        """ 判断item的类型，并作相应的处理，再入数据库 """
        if isinstance(item, CategoriesItem):
            try:
                self.Categories.insert(dict(item))
            except Exception:
                pass
        elif isinstance(item, ProductsItem):
            try:
                self.Products.insert(dict(item))
            except Exception:
                pass
        elif isinstance(item, ShopItem):
            try:
                self.Shop.insert(dict(item))
            except Exception:
                pass
        elif isinstance(item, CommentItem):
            try:
                self.Comment.insert(dict(item))
            except Exception:
                pass
        elif isinstance(item, CommentImageItem):
            try:
                self.CommentImage.insert(dict(item))
            except Exception:
                pass
        elif isinstance(item, CommentSummaryItem):
            try:
                self.CommentSummary.insert(dict(item))
            except Exception:
                pass
        elif isinstance(item, HotCommentTagItem):
            try:
                self.HotCommentTag.insert(dict(item))
            except Exception:
                pass
        return item