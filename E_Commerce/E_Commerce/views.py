from django.conf import settings
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import redirect,render
from app.models import slider,banner_area,Main_Category,Product,Category,Color,Brand,Coupon_code,Order,OrderItem,wishlist
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Min ,Sum
from django.contrib.auth.decorators import login_required
from cart.cart import Cart
from django.views.decorators.csrf import csrf_exempt

import razorpay



client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET))

def BASE(request):
    return render(request,'base.html')


def HOME(request):
    sliders = slider.objects.all().order_by('-id')[0:3]
    banners = banner_area.objects.all().order_by('-id')[0:3]

    main_category = Main_Category.objects.all()
    product = Product.objects.filter(section__name = "Top Deals Of The Day")


    context = {
        'sliders':sliders,
        'banners':banners,
        'main_category':main_category,
        'product' :product
    }
    return render(request,'Main/home.html',context)

def PRODUCT_DETAILS(request,slug):

    product = Product.objects.filter(slug = slug)

    if product.exists():
        product = Product.objects.get(slug=slug)
    else:
        return redirect('404')

    context={

        'product':product,

    }
    return render(request,'product/product_detail.html',context)


def ERROR404(request):

    return render(request,'errors/404.html')


def MY_ACCOUNT(request):
    return render(request,'account/my-account.html')


def REGISTER(request):
    if request.method =="POST":
        username = request.POST.get('username')
        email =  request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username = username).exists():
            messages.error(request,'username already exists')
            return redirect('login')

        if User.objects.filter(email = email).exists():
            messages.error(request,'email already exists')
            return redirect('login')


        user = User(
            username = username,
            email = email,

        )
        user.set_password(password)
        user.save()

        return redirect('login')



def LOGIN(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username = username, password = password)
        if user is not None:
            login(request,user)
            return redirect('home')
        else:
            messages.error(request,'Email Or Password Invalid !!')
            return redirect('login')

@login_required(login_url='/accounts/login/')
def PROFILE(request):
    return render(request,'profile/profile.html')


@login_required(login_url='/accounts/login/')
def PROFILE_UPDATE(request):
    if request.method == "POST":
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_id = request.user.id

        user = User.objects.get(id=user_id)
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.email = email

        if password != None and password != "":
            user.set_password(password)
        user.save()
        messages.success(request,'Profile Updated Successfully...')

        return redirect('profile')


def ABOUT(request):
    return render(request,'main/about.html')


def CONTACT(request):
    return render(request,'main/contact.html')


def PRODUCT(request):
    category = Category.objects.all()
    product = Product.objects.all()
    color = Color.objects.all()
    brand = Brand.objects.all()

    min_price = Product.objects.all().aggregate(Min('price'))
    max_price = Product.objects.all().aggregate(Max('price'))
    ColorID = request.GET.get('colorID')
    BrandID = request.GET.get('brandID')
    CatID = request.GET.get('catID')

    FilterPrice = request.GET.get('FilterPrice')
    if FilterPrice:
        Int_FilterPrice = int(FilterPrice)
        product = Product.objects.filter(price__lte=Int_FilterPrice)
    elif ColorID:
        product = Product.objects.filter(color=ColorID)
    elif BrandID:
        product = Product.objects.filter(Brand=BrandID)
    elif CatID:
        product = Product.objects.filter(Categories=CatID)

    else:
        product = Product.objects.all()





    context = {
        'category':category,
        'product':product,
        'min_price': min_price,
        'max_price': max_price,
        'FilterPrice': FilterPrice,
        'color': color,
        'brand': brand,
    }
    return render(request,'product/product.html',context)

def filter_data(request):
    categories = request.GET.getlist('category[]')
    brands = request.GET.getlist('brand[]')

    brand = request.GET.getlist('brand[]')
    print(brand)

    allProducts = Product.objects.all().order_by('-id').distinct()
    if len(categories) > 0:
        allProducts = allProducts.filter(Categories__id__in=categories).distinct()

    if len(brands) > 0:
        allProducts = allProducts.filter(Brand__id__in=brands).distinct()


    t = render_to_string('ajax/product.html', {'product': allProducts})

    return JsonResponse({'data': t})


def SEARCH(request):
    query = request.GET.get('query')
    product = Product.objects.filter(product_name__icontains = query)
    context = {
        'product':product
    }

    return render(request,'main/search.html',context)




@login_required(login_url="/accounts/login/")
def cart_add(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.add(product=product)
    return redirect("cart_detail")


@login_required(login_url="/accounts/login/")
def item_clear(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.remove(product)
    return redirect("cart_detail")


@login_required(login_url="/accounts/login/")
def item_increment(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.add(product=product)
    return redirect("cart_detail")


@login_required(login_url="/accounts/login/")
def item_decrement(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.decrement(product=product)
    return redirect("cart_detail")


@login_required(login_url="/accounts/login/")
def cart_clear(request):
    cart = Cart(request)
    cart.clear()
    return redirect("cart_detail")


@login_required(login_url="/accounts/login/")
def cart_detail(request):
    cart = request.session.get('cart')
    # packing_cost = sum(i['packing_cost'] for i in cart.values() if i)
    # tax = sum(i['tax'] for i in cart.values() if i)

    coupon = None
    valid_coupon = None
    invalid_coupon = None

    if request.method =="GET":
        coupon_code = request.GET.get('coupon_code')
        if coupon_code:
            try:
                coupon = Coupon_code.objects.get(code = coupon_code)
                valid_coupon = "Are Applicable on Current Order !"
            except:
                invalid_coupon = "Invalid Coupon Code !"

    context ={
        # 'packing_cost':packing_cost,
        # 'tax':tax,
        'coupon':coupon,
        'valid_coupon':valid_coupon,
        'invalid_coupon':invalid_coupon

    }
    return render(request, 'cart/cart.html',context)


def checkout(request):
    amount_str = request.POST.get('amount')
    amount_float = float(amount_str)
    amount = int(amount_float * 100)
    payment = client.order.create({
        "amount":amount,
        "currency":"INR",
        "payment_capture":"1"
    })
    order_id = payment['id']
    coupon_discount=None
    if request.method == "POST":
        coupon_discount = request.POST.get('coupon_discount')
    cart = request.session.get('cart')
    # packing_cost = sum(i['packing_cost'] for i in cart.values() if i)
    # tax = sum(i['tax'] for i in cart.values() if i)
    # tax_and_packing_cost = (packing_cost + tax)



    context ={
        # 'tax_and_packing_cost' : tax_and_packing_cost,
        'coupon_discount' : coupon_discount,
        'payment' : payment,
        'order_id' : order_id,
    }




    return render(request,'checkout/checkout.html',context)


def placeorder(request):
    if request.method == 'POST':
        uid = request.session.get('_auth_user_id')
        user = User.objects.get(id=uid)
        cart = request.session.get('cart')


        country = request.POST.get('country')
        order_id = request.POST.get('order_id')
        payment = request.POST.get('payment')
        firstname = request.POST.get('first_name')
        lastname = request.POST.get('last_name')
        address = request.POST.get('address1')
        city = request.POST.get('city')
        state = request.POST.get('state')
        postcode = request.POST.get('postcode')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        amount = request.POST.get('amount')

        context ={
            'order_id':order_id

        }

        order = Order(
            user=user,
            country=country,
            firstname=firstname,
            lastname=lastname,
            address=address,
            city =city,
            state=state,
            postcode=postcode,
            email=email,
            phone=phone,
            payment_id=order_id,
            amount=amount




        )
        order.save()

        for i in cart:
            a = cart[i]['price']
            b = cart[i]['quantity']
            total = a*b

            item = OrderItem(
                order = order,
                product = cart[i]['product_name'],
                image = cart[i]['featured_image'],
                quantity = cart[i]['quantity'],
                price = cart[i]['price'],
                total = total


            )
            item.save()




        return render(request,'checkout/placeorder.html',context)

@csrf_exempt
def success(request):
    if request.method == "POST":
        a = request.POST
        order_id = ""
        for key, val in a.items():
            if key == 'razorpay_order_id':
                order_id = val
                break
        user = Order.objects.filter(payment_id = order_id).first()
        user.paid = True
        user.save()

    return render(request,'checkout/thankyou.html')


def FAQS(request):

    return render(request,'main/faqs.html')


