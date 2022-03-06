from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from .models import Cart, CartItem
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required


# Create your views here.

# session id function
def _cart_id(request):
    # if there is a session
    cart = request.session.session_key

    # if there's no session
    if not cart:
        cart = request.session.create()

    return cart # returns the value of the function basic python


def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)  # get the product
    product_variation = []

    # If the user is authenticated
    if current_user.is_authenticated:
        if request.method == 'POST':
            for item in request.POST: # extracting key from dictionary structure of request.POST
                key = item
                value = request.POST[key]

                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key,
                                                      variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass

            # color = request.POST['color'] 'color' take from name='color' in html parameters
            # size = request.POST['size']
            # print(color, size) to check in POST method output in terminal
            # return HttpResponse(color + ' ' + size)  to check in GET method output in template
            # exit()

            is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()

            if is_cart_item_exists:
                cart_item = CartItem.objects.filter(product=product, user=current_user)
                ex_var_list = []
                id = []
                for item in cart_item:
                    existing_variation = item.variations.all()
                    ex_var_list.append(list(existing_variation))
                    id.append(item.id)

                # Check if there is existing variation of the item
                if product_variation in ex_var_list:

                    # increase the cart item quantity
                    index = ex_var_list.index(product_variation) # to get the index of ex_var_list list
                    # print(index)

                    item_id = id[index] # existing id of existing cart item
                    # print(item_id)

                    item = CartItem.objects.get(product=product, id=item_id)
                    item.quantity += 1
                    item.save()
                else:
                    # create new cart item with different variation
                    item = CartItem.objects.create(product=product, quantity=1, user=current_user)
                    # print(type(item.variations))
                    if len(product_variation) > 0:
                        item.variations.clear()
                        item.variations.add(*product_variation)
                    item.save()

            else:
                cart_item = CartItem.objects.create(product=product, quantity=1, user=current_user)
                if len(product_variation) > 0:
                    cart_item.variations.clear()
                    cart_item.variations.add(*product_variation)
                cart_item.save()

            # return HttpResponse(cart_item.products)
            # exit()
            # print(type(product_variation))  # use this to check result list of variation queryset
            return redirect('cart')

    # If the user is not authenticated
    else:
        product_variation = []
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]

                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key,
                                                      variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass

        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))  # get the cart using the cart_id present in the session
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request)) # creating cart
            cart.save()

        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()

        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)

            # Check if there is existing variation of the item
            if product_variation in ex_var_list:
                # increase the cart item quantity
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
            else:
                # create new cart item with different variation
                item = CartItem.objects.create(product=product, quantity=1, cart=cart)
                # print(type(item.variations))
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()

        else:
            cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart) # creating cart item
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()

        # return HttpResponse(cart_item.products)
        # exit()
        # print(product_variation)  # use this to check result
        return redirect('cart')


def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()

        else:
            cart_item.delete()
    except:
        pass # just ignore

    return redirect('cart')


def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(cart=cart, product=product, id=cart_item_id)

    cart_item.delete()

    return redirect('cart')


def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0

        # Logged in users use user = request.user
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)

        # Non logged in users use cart=cart
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            print(cart)
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
        tax = (2 * total) / 100
        grand_total = total + tax

        # return HttpResponse(cart_item.variations.price)
        # exit()

    except ObjectDoesNotExist:
        pass  # just ignore

    context = {
        'total': total,
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
        tax = (2 * total) / 100
        grand_total = total + tax

        # return HttpResponse(cart_item.variations.price)
        # exit()

    except ObjectDoesNotExist:
        pass  # just ignore

    context = {
        'total': total,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total
    }
    print(cart_items)
    return render(request, 'store/checkout.html', context)
