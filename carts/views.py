from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from .models import CartItem, Cart
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

# Create your views here.


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)

    if current_user.is_authenticated:

        product_variation = []

        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]

                try:
                    variation_instance = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation_instance)
                except Variation.DoesNotExist:
                    pass

        is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()
        if is_cart_item_exists:
            cart_items = CartItem.objects.filter(product=product, user=current_user)

            for cart_item in cart_items:
                # Check if all variations match
                if set(cart_item.variations.all()) == set(product_variation):
                    cart_item.quantity += 1
                    cart_item.save()
                    break
            else:
                # If no matching cart item found, create a new one
                new_cart_item = CartItem.objects.create(product=product, quantity=1, user=current_user)
                new_cart_item.variations.set(product_variation)
                new_cart_item.save()
        else:
            # If no cart item exists, create a new one
            new_cart_item = CartItem.objects.create(product=product, quantity=1, user=current_user)
            new_cart_item.variations.set(product_variation)
            new_cart_item.save()

        return redirect('cart')

    else:

        product_variation = []

        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]

                try:
                    variation_instance = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation_instance)
                except Variation.DoesNotExist:
                    pass

        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id=_cart_id(request)
            )
        cart.save()

        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
        if is_cart_item_exists:
            cart_items = CartItem.objects.filter(product=product, cart=cart)

            for cart_item in cart_items:
                # Check if all variations match
                if set(cart_item.variations.all()) == set(product_variation):
                    cart_item.quantity += 1
                    cart_item.save()
                    break
            else:
                # If no matching cart item found, create a new one
                new_cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
                new_cart_item.variations.set(product_variation)
                new_cart_item.save()
        else:
            # If no cart item exists, create a new one
            new_cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
            new_cart_item.variations.set(product_variation)
            new_cart_item.save()

        return redirect('cart')


def remove_cart(request, product_id):
    
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(product=product, user=request.user)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))     
        cart_items = CartItem.objects.filter(product=product, cart=cart)

    if cart_items.exists():
        # If there are multiple items, decrease quantity of each
        for cart_item in cart_items:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()

    return redirect('cart')

def remove_cart_item(request, product_id):
    
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart_item = CartItem.objects.filter(product=product, user=request.user).first()
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))    
        cart_item = CartItem.objects.filter(product=product, cart=cart).first()

    if cart_item:
        cart_item.delete()

    return redirect('cart')
# def cart(request, total=0, quantity=0, cart_item=None):
#     try:
#         tax = 0
#         grand_total = 0
#         if request.user.is_authenticated:
#            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
#         else:
#            cart = Cart.objects.get(cart_id=_cart_id(request))
#            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
#         for cart_item in cart_items:
#             total += (cart_item.product.price * cart_item.quantity)
#             quantity += cart_item.quantity

#         tax = (2 * total) / 100
#         grand_total = total + tax
#     except ObjectDoesNotExist:
#         pass

#     context = {
#         'total': total,
#         'quantity': quantity,
#         'cart_items': cart_items,
#         'tax': tax,
#         'grand_total': grand_total
#     }

#     return render(request, 'store/cart.html', context)

def cart(request):
    total = 0
    quantity = 0
    cart_items = []  # Initialize cart_items as an empty list

    try:
        tax = 0
        grand_total = 0

        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

        tax = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total
    }

    return render(request, 'store/cart.html', context)


@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):

    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
           cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
           cart = Cart.objects.get(cart_id=_cart_id(request))
           cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

        tax = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total
    }
    return render(request, 'store/checkout.html', context)    
