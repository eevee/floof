<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="artlib" file="/art/lib.mako" />

<%def name="title()">${target_user.name}'s albums</%def>

## TODO needs a link back to user's art or user's page or something.  maybe a user bar across the top

<section>
    <h1>${title()}</h1>

    <ul class="standard-list">
        % for album in request.user.permitted('album.view', target_user.albums):
        <li>${artlib.album_link(album)}</li>
        % endfor
    </ul>
</section>

% if request.user == target_user:
## TODO maybe this should be the JS version by default
<section>
    <h1>New album</h1>

    <%lib:secure_form>
    <fieldset>
        <dl>
            <dt>Name</dt>
            <dd><input type="text" name="name"></dd>
            <dt>Privacy</dt>
            <dd>
                <ul>
                    ## TODO this is duplicated from art/lib.mako; sucks.  need real enum support??
                    <li>
                        <label>
                            ${h.tags.radio(name='privacy', value='gallery')}
                            ${lib.icon('photo-album-blue')} Gallery
                        </label>
                    </li>
                    <li>
                        <label>
                            ${h.tags.radio(name='privacy', value='public')}
                            ${lib.icon('book-bookmark')} Public
                        </label>
                    </li>
                    <li>
                        <label>
                            ${h.tags.radio(name='privacy', value='private')}
                            ${lib.icon('book-brown')} Private
                        </label>
                    </li>
                    ##<li>${lib.icon('plug')} Plug</li>
                </ul>
            </dd>
        </dl>
        <footer>
            <button type="submit">Create</button>
        </footer>
    </fieldset>
    </%lib:secure_form>
</section>
% endif
