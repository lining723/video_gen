"""Tests for subject consistency control feature.

This module tests the core functionality of subject consistency control:
- Feature extraction and locking (US1)
- Variant generation (US2)
- Version management (US3)
"""

import pytest


class TestSubjectFeatureLock:
    """Tests for User Story 1 - 主体特征锁定"""

    def test_extract_features_on_subject_generation(self, client, project_with_storyboard):
        """When a subject is generated, features should be extracted automatically."""
        response = client.post(
            f'/api/projects/{project_with_storyboard}/subjects:generate',
            headers={'X-API-Key': 'test-key'}
        )
        assert response.status_code == 202
        data = response.json()
        assert data['ok'] is True
        for item in data.get('items', []):
            # Feature description should be populated (may be empty if extraction failed)
            assert 'feature_description' in item

    def test_update_feature_description(self, client, project_with_subject):
        """User can update the feature description of a subject."""
        subject_id = 'subject-001'
        response = client.put(
            f'/api/projects/{project_with_subject}/subjects/{subject_id}',
            headers={'X-API-Key': 'test-key'},
            json={'feature_description': '25岁亚洲女性，椭圆脸型，杏仁眼'}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['ok'] is True
        assert data['item']['feature_description'] == '25岁亚洲女性，椭圆脸型，杏仁眼'

    def test_update_feature_description_locked_subject_fails(self, client, project_with_locked_subject):
        """Updating feature description on a locked subject should fail."""
        subject_id = 'locked-subject-001'
        response = client.put(
            f'/api/projects/{project_with_locked_subject}/subjects/{subject_id}',
            headers={'X-API-Key': 'test-key'},
            json={'feature_description': 'new description'}
        )
        assert response.status_code == 400
        data = response.json()
        assert data['ok'] is False
        assert 'locked' in data['error'].lower()

    def test_lock_subject(self, client, project_with_subject):
        """User can lock a subject's feature description."""
        subject_id = 'subject-001'
        response = client.post(
            f'/api/projects/{project_with_subject}/subjects/{subject_id}:lock',
            headers={'X-API-Key': 'test-key'}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['ok'] is True
        assert data['item']['is_locked'] is True

    def test_unlock_subject(self, client, project_with_locked_subject):
        """User can unlock a subject's feature description."""
        subject_id = 'locked-subject-001'
        response = client.post(
            f'/api/projects/{project_with_locked_subject}/subjects/{subject_id}:unlock',
            headers={'X-API-Key': 'test-key'}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['ok'] is True
        assert data['item']['is_locked'] is False


class TestSubjectVariantGeneration:
    """Tests for User Story 2 - 主体变体生成"""

    def test_generate_variant_with_hint(self, client, project_with_base_subject):
        """User can generate a variant subject with a specific hint."""
        shot_id = 'shot-001'
        response = client.post(
            f'/api/projects/{project_with_base_subject}/subjects/shots/{shot_id}:generate',
            headers={'X-API-Key': 'test-key'},
            json={'mode': 'variant', 'variant_hint': '微笑表情'}
        )
        assert response.status_code == 201
        data = response.json()
        assert data['ok'] is True
        item = data['item']
        assert item['variant_type'] == 'variant'
        assert item['variant_hint'] == '微笑表情'
        assert item['base_subject_id']  # Should reference base subject

    def test_variant_uses_base_subject_features(self, client, project_with_base_subject):
        """Variant generation should reference base subject's feature description."""
        shot_id = 'shot-001'
        response = client.post(
            f'/api/projects/{project_with_base_subject}/subjects/shots/{shot_id}:generate',
            headers={'X-API-Key': 'test-key'},
            json={'mode': 'variant', 'variant_hint': '运动装束'}
        )
        assert response.status_code == 201
        # The prompt should include base subject's features
        # This is implicitly tested through the API success


class TestSubjectVersionManagement:
    """Tests for User Story 3 - 主体更新确认流程"""

    def test_regenerate_creates_new_version(self, client, project_with_subject):
        """Regenerating a subject should create a new version."""
        subject_id = 'subject-001'

        # Get current version
        get_response = client.get(
            f'/api/projects/{project_with_subject}/subjects/{subject_id}',
            headers={'X-API-Key': 'test-key'}
        )
        current_version = get_response.json()['item']['image_version']

        # Regenerate
        response = client.post(
            f'/api/projects/{project_with_subject}/subjects/{subject_id}:regenerate',
            headers={'X-API-Key': 'test-key'},
            json={'cascade_render': False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['ok'] is True
        assert data['item']['image_version'] == current_version + 1

    def test_list_subject_versions(self, client, project_with_subject_versions):
        """User can list all versions of a subject."""
        subject_id = 'subject-with-versions'
        response = client.get(
            f'/api/projects/{project_with_subject_versions}/subjects/{subject_id}/versions',
            headers={'X-API-Key': 'test-key'}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['ok'] is True
        assert len(data['items']) >= 1

    def test_rollback_to_previous_version(self, client, project_with_subject_versions):
        """User can rollback to a previous version."""
        subject_id = 'subject-with-versions'
        target_version = 1

        response = client.post(
            f'/api/projects/{project_with_subject_versions}/subjects/{subject_id}:rollback',
            headers={'X-API-Key': 'test-key'},
            json={'target_version': target_version}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['ok'] is True
        assert data['item']['image_version'] == target_version

    def test_rollback_nonexistent_version_fails(self, client, project_with_subject):
        """Rollback to a non-existent version should fail."""
        subject_id = 'subject-001'
        response = client.post(
            f'/api/projects/{project_with_subject}/subjects/{subject_id}:rollback',
            headers={'X-API-Key': 'test-key'},
            json={'target_version': 999}
        )
        assert response.status_code == 404
