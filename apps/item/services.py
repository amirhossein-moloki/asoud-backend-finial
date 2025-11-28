from typing import Dict
from apps.item.models import Item, ItemDiscount
from apps.users.models import User
from apps.base.exceptions import BusinessLogicException
from apps.advertise.core import AdvertisementCore
from .serializers.owner_serializers import ItemDiscountCreateSerializer

class ItemService:
    """
    Business logic service for item operations.
    """

    def create_item(self, user: User, item_data: Dict) -> Item:
        """
        Creates a new item with the given data.

        Args:
            user: The user creating the item.
            item_data: A dictionary containing the item data.

        Returns:
            The newly created item.
        """
        item = Item.objects.create(**item_data)
        if item.is_requirement:
            AdvertisementCore.create_advertisement_for_item(item)
        return item


class ItemDiscountService:
    """
    Business logic service for item discount operations.
    """

    def create_item_discount(self, item: Item, discount_data: Dict) -> Item:
        """
        Applies a discount to the given item.

        Args:
            item: The item to apply the discount to.
            discount_data: A dictionary containing the discount data.

        Returns:
            The updated item with the discount applied.
        """
        serializer = ItemDiscountCreateSerializer(data=discount_data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(item=item)
            percentage = serializer.validated_data.get('percentage')
            item.main_price = item.main_price - (item.main_price * percentage / 100)
            item.save()
            return item


class ItemShippingService:
    """
    Business logic service for item shipping operations.
    """

    def create_item_shipping(self, item: Item, shipping_data: Dict) -> Item:
        """
        Creates a new shipping option for the given item.

        Args:
            item: The item to create the shipping option for.
            shipping_data: A dictionary containing the shipping data.

        Returns:
            The item with the new shipping option.
        """
        item.ships.create(**shipping_data)
        return item
