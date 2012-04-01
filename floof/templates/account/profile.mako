<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<section>
    ${lib.secure_form('')}
        <textarea name="profile" rows="40" cols="120">${request.user.profile or ''}</textarea>
        <br>
        <input type="submit" value="Update">
    ${h.end_form()}
</section>
