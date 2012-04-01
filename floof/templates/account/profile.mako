<%inherit file="base.mako" />

<form action="" method="POST">
<textarea name="profile" rows="40" cols="120">${request.user.profile or ''}</textarea>
<br>
<input type="submit" value="Update">
</form>
