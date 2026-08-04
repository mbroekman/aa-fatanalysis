# FAT Analysis

Alliance Auth plugin for analyzing FATs (Fleet Activity Tracking). This plugin allows for the upload of 30-day and 90-day FAT CSV files, parses them dynamically, and provides overviews and interactive charts on both a per-character and per-corporation basis.

## Installation

1. **Activate your Alliance Auth virtual environment**
   ```bash
   source /home/allianceserver/venv/auth/bin/activate
   ```

2. **Install the plugin**
   Navigate to the directory containing this plugin and run:
   ```bash
   pip install -e .
   ```
   *(Or install via git / pip once published to a repository)*

3. **Update your Alliance Auth settings**
   Add `'fatanalysis'` to your `INSTALLED_APPS` in `myauth/myauth/settings/local.py`:
   ```python
   INSTALLED_APPS += [
       'fatanalysis',
   ]
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Restart Alliance Auth services**
   ```bash
   sudo systemctl restart supervisor
   ```
   *(Or restart gunicorn and celery according to your specific setup)*

## Permissions
Assign the `fatanalysis.basic_access` permission in the admin panel to any user or group that should have access to view and upload FAT analysis data.
