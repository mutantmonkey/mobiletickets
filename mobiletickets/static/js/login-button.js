function disable_enable(login_button)
{
    if (login_button.value == 'Login')
    {   
        document.getElementById('login-logout').value='Logout';
		document.getElementById('m-login-logout').value='Logout';
        window.open('https://auth.vt.edu/','mywindow');
    }
    else
    {
        document.getElementById('login-logout').value='Login';
    }
}
