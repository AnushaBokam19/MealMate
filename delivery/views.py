from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.contrib import messages
import razorpay

from .models import Customer, Restaurant, Item, Cart


# Home Page
def index(request):
    return render(request, 'delivery/index.html')


# Open Signup Page
def open_signup(request):
    return render(request, 'delivery/signup.html')


# Open Signin Page
def open_signin(request):
    return render(request, 'delivery/signin.html')


# Signup
def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        address = request.POST.get('address')

        try:
            Customer.objects.get(username=username)
            return HttpResponse("Duplicate username!")

        except Customer.DoesNotExist:
            Customer.objects.create(
                username=username,
                password=password,
                email=email,
                mobile=mobile,
                address=address,
            )

    return render(request, 'delivery/signin.html')


# Signin
def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            Customer.objects.get(
                username=username,
                password=password
            )

            if username == 'admin':
                return render(
                    request,
                    'delivery/admin_home.html'
                )

            else:
                restaurantList = Restaurant.objects.all()

                return render(
                    request,
                    'delivery/customer_home.html',
                    {
                        "restaurantList": restaurantList,
                        "username": username
                    }
                )

        except Customer.DoesNotExist:
            return HttpResponse("Registration failed")

    return render(request, 'delivery/signin.html')


# Open Add Restaurant Page
def open_add_restaurant(request):
    return render(request, 'delivery/add_restaurant.html')


# Add Restaurant
def add_restaurant(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')

        try:
            Restaurant.objects.get(name=name)
            return HttpResponse("Duplicate restaurant!")

        except Restaurant.DoesNotExist:
            Restaurant.objects.create(
                name=name,
                picture=picture,
                cuisine=cuisine,
                rating=rating,
            )

    return render(request, 'delivery/admin_home.html')


# Show Restaurants
def open_show_restaurant(request):
    restaurantList = Restaurant.objects.all()

    return render(
        request,
        'delivery/show_restaurants.html',
        {
            "restaurantList": restaurantList
        }
    )


# Open Update Restaurant
def open_update_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)

    return render(
        request,
        'delivery/update_restaurant.html',
        {
            'restaurant': restaurant
        }
    )


# Update Restaurant
def update_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')

        restaurant.name = name
        restaurant.picture = picture
        restaurant.cuisine = cuisine
        restaurant.rating = rating

        restaurant.save()

    restaurantList = Restaurant.objects.all()

    return render(
        request,
        'delivery/show_restaurants.html',
        {
            "restaurantList": restaurantList
        }
    )


# Delete Restaurant
def delete_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)

    restaurant.delete()

    restaurantList = Restaurant.objects.all()

    return render(
        request,
        'delivery/show_restaurants.html',
        {
            "restaurantList": restaurantList
        }
    )


# Open Update Menu
def open_update_menu(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)

    itemList = restaurant.items.all()

    return render(
        request,
        'delivery/update_menu.html',
        {
            "itemList": itemList,
            "restaurant": restaurant
        }
    )


# Update Menu / Add Item
def update_menu(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        vegeterian = request.POST.get('vegeterian') == 'on'
        picture = request.POST.get('picture')

        try:
            Item.objects.get(name=name)

            return HttpResponse("Duplicate item!")

        except Item.DoesNotExist:
            Item.objects.create(
                restaurant=restaurant,
                name=name,
                description=description,
                price=price,
                vegeterian=vegeterian,
                picture=picture,
            )

    return render(request, 'delivery/admin_home.html')


# Delete Menu Item
def delete_menu_item(request, item_id, restaurant_id):
    item = Item.objects.get(id=item_id)

    item.delete()

    return redirect(
        'open_update_menu',
        restaurant_id
    )


# View Restaurant Menu
def view_menu(request, restaurant_id, username):
    restaurant = Restaurant.objects.get(id=restaurant_id)

    itemList = restaurant.items.all()

    return render(
        request,
        'delivery/customer_menu.html',
        {
            "itemList": itemList,
            "restaurant": restaurant,
            "username": username
        }
    )


# Add Item To Cart
def add_to_cart(request, item_id, username):
    item = Item.objects.get(id=item_id)

    customer = Customer.objects.get(username=username)

    cart, created = Cart.objects.get_or_create(
        customer=customer
    )

    cart.items.add(item)

    messages.success(
        request,
        f"{item.name} added to cart!"
    )

    return redirect(
        'view_menu',
        item.restaurant.id,
        username
    )


# Show Cart
def show_cart(request, username):
    customer = Customer.objects.get(username=username)

    cart = Cart.objects.filter(
        customer=customer
    ).first()

    items = cart.items.all() if cart else []

    total_price = cart.total_price() if cart else 0

    return render(
        request,
        'delivery/cart.html',
        {
            "itemList": items,
            "total_price": total_price,
            "username": username
        }
    )


# Remove Item From Cart
def remove_from_cart(request, item_id, username):
    customer = Customer.objects.get(username=username)

    cart = Cart.objects.filter(
        customer=customer
    ).first()

    if cart:
        item = Item.objects.get(id=item_id)

        cart.items.remove(item)

    return redirect(
        'show_cart',
        username
    )


# Checkout
def checkout(request, username):

    # Get customer
    customer = get_object_or_404(
        Customer,
        username=username
    )

    # Get customer's cart
    cart = Cart.objects.filter(
        customer=customer
    ).first()

    # Get cart items
    cart_items = cart.items.all() if cart else []

    # Calculate total
    total_price = cart.total_price() if cart else 0

    # Check empty cart
    if total_price == 0:

        return render(
            request,
            'delivery/checkout.html',
            {
                'username': username,
                'error': 'Your cart is empty!'
            }
        )

    # Check Razorpay credentials
    if not settings.RAZORPAY_KEY_ID:

        return render(
            request,
            'delivery/checkout.html',
            {
                'username': username,
                'cart_items': cart_items,
                'total_price': total_price,
                'error': 'Razorpay Key ID is missing.'
            }
        )

    if not settings.RAZORPAY_KEY_SECRET:

        return render(
            request,
            'delivery/checkout.html',
            {
                'username': username,
                'cart_items': cart_items,
                'total_price': total_price,
                'error': 'Razorpay Key Secret is missing.'
            }
        )

    try:

        # Create Razorpay client
        client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET
            )
        )

        # Convert rupees to paise
        amount = int(float(total_price) * 100)

        # Razorpay order data
        order_data = {
            'amount': amount,
            'currency': 'INR',
            'payment_capture': 1
        }

        # Create Razorpay order
        order = client.order.create(
            data=order_data
        )

        # Send data to checkout page
        return render(
            request,
            'delivery/checkout.html',
            {
                'username': username,
                'cart_items': cart_items,
                'total_price': total_price,
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                'order_id': order['id'],
                'amount': amount,
            }
        )

    except Exception as e:

        # Print actual error in terminal
        print("===================================")
        print("RAZORPAY ERROR:")
        print(e)
        print("===================================")

        return render(
            request,
            'delivery/checkout.html',
            {
                'username': username,
                'cart_items': cart_items,
                'total_price': total_price,
                'error': 'Unable to connect to Razorpay. Please try again.'
            }
        )


# Orders Page
def orders(request, username):

    customer = get_object_or_404(
        Customer,
        username=username
    )

    cart = Cart.objects.filter(
        customer=customer
    ).first()

    # Get cart items before clearing
    cart_items = cart.items.all() if cart else []

    # Get total before clearing
    total_price = cart.total_price() if cart else 0

    # Clear cart
    if cart:
        cart.items.clear()

    return render(
        request,
        'delivery/orders.html',
        {
            'username': username,
            'customer': customer,
            'cart_items': cart_items,
            'total_price': total_price,
        }
    )