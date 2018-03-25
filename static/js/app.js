let walletId = null;
const REFRESH_DURATION = 60000; // 1min

const updateInfo = () => {
    //Update user info.
    $('div.users').html('<h3>Online:</h3>');
    request({operation: 'list'}, (resp) => {
        resp.info.users_list.filter((user) =>
            user.id !== walletId
        ).forEach((user) => {
            const liElem = document.createElement("li");
            liElem.innerHTML = '<a href="#" class="transact" data:id="' + user.id + '">#' + user.name +'</a>';
            $('div.users').append(liElem);
        });
    });

    //Update wallet info.
    request({
        operation: 'fetch',
        wallet_id: walletId
    }, (data) => {
        if(data.code == 200) {
            $('#dashboard .balance').text('CC ' + data.info.balance);
        }
    })
};

const populate = (data) => {
    if(data.code != 200) {
        alert(data.message);
        return;
    }

    $('#login').css('display', 'none');
    $('#dashboard').css('display', 'block');            
    
    updateInfo(); // Initial call
    setInterval(updateInfo, REFRESH_DURATION); //Update dashboard info every x sec/min.

    const info = data.info;
    $('#dashboard .balance').text('CC ' + info.balance);
    $('#dashboard .wallet_id').text('Wallet ID: ' + info.id);
    walletId = info.id;
}

const request = (data, cb) => {
    $.ajax({
        url: '/api',
        data: data,
        method: 'post',
        async: 'false'
    }).done((resp) => {
        cb(JSON.parse(resp));
    });
};

$('.users').on('click', 'li', (ev) => {
    ev.preventDefault();
    const receiverWallet = $(ev.target).attr('data:id');
    const amount = prompt('Enter Amount to be paid', '1.0');

    if(amount == null || isNaN(amount)) {
        return;
    }

    request({
        operation: 'transact',
        sender: walletId,
        receiver: receiverWallet,
        amount: amount
    }, (resp) => {
        if(resp.code == 200) {
            console.log('Transaction completed with id: ' + resp.info.transaction_id);
            $('#dashboard .balance').text('CC ' + resp.info.balance);
        } else {
            alert('Transaction Failed');
        }
    })
});

$('#username').keyup((ev) => {
    const elem = $(ev.target);
    const isDisabled = !(elem.val() && elem.val().replace(/ /g,'').length > 0); 
    $('.login_btn').attr('disabled', isDisabled);
    $('.signup_btn').attr('disabled', isDisabled);
});

$('.login_btn').click((ev) => {
    const value = $('#username').val();
    $('#username').val('');

    request({
        wallet_id: value,
        operation: 'login'
    }, populate);
});

$('.signup_btn').click((ev) => {
    const value = $('#username').val();
    $('#username').val('');

    request({
        username: value,
        operation: 'add'
    }, populate);
});

$('.logout').click((ev) => {
    clearInterval(updateInfo);

    request({
        operation: 'logout',
        wallet_id: walletId
    }, (resp) => {
        if(resp.code == 200) {
            $('#dashboard').css('display', 'none');
            $('#login').css('display', 'block');
            $('div.users').html('<h3>Online:</h3>');
            walletId = null;
        } else {
            alert(resp.message);
        }
    });
});