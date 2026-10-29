"""Pinned, attributed country/flag pairs, checked before a question is used."""
import hashlib
import json
from pathlib import Path
import re

from PIL import Image
from .paths import resource_root


class CatalogError(ValueError):
    pass


class Catalog:
    def __init__(self, assets_root=None):
        self.root = Path(assets_root) if assets_root is not None else resource_root()/'assets'
        try:
            data = json.loads((self.root/'countries.json').read_text(encoding='utf-8'))
        except (OSError, ValueError) as exc:
            raise CatalogError(f'국가 데이터 읽기 실패: {exc}') from exc
        manifest_path = self.root/'asset_manifest.json'
        if manifest_path.exists() or assets_root is None:
            try:
                manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
                source_path = self.root/'country_source_upstream.json'
                if hashlib.sha256((self.root/'countries.json').read_bytes()).hexdigest() != manifest['country_manifest_sha256']:
                    raise CatalogError('배포 국가 데이터 해시가 일치하지 않습니다. 원본 에셋을 복구하세요.')
                if hashlib.sha256(source_path.read_bytes()).hexdigest() != manifest['upstream_country_data_sha256']:
                    raise CatalogError('원본 국가 코드·이름 데이터가 변경됐습니다.')
                expected_names = {row['code']: row['name'] for row in json.loads(source_path.read_text(encoding='utf-8'))}
                for row in data:
                    if row.get('name') != expected_names.get(row.get('code')):
                        raise CatalogError('국가 코드와 원본 영어 이름의 연결이 일치하지 않습니다.')
            except (OSError, KeyError, TypeError, ValueError) as exc:
                if isinstance(exc, CatalogError):
                    raise
                raise CatalogError(f'국가·국기 출처 검증 실패: {exc}') from exc
        if not isinstance(data, list) or len(data) < 4:
            raise CatalogError('국가 데이터는 4개 이상의 국가 목록이어야 합니다.')
        codes, names = set(), set()
        for row in data:
            if not isinstance(row, dict) or not re.fullmatch('[a-z]{2}', str(row.get('code', ''))):
                raise CatalogError('국가 ISO alpha-2 코드가 올바르지 않습니다.')
            code, name = row['code'], row.get('name')
            if code in codes or not isinstance(name, str) or not name.strip() or name in names:
                raise CatalogError('국가 코드 또는 영어 이름이 비어 있거나 중복됩니다.')
            if row.get('difficulty') not in ('Easy', 'Normal', 'Hard'):
                raise CatalogError(f'국가 난이도 오류: {code}')
            flag = Path(str(row.get('flag', '')))
            # The code itself selects the image; arbitrary path remapping is refused.
            if flag.as_posix() != f'flags/{code}.png':
                raise CatalogError(f'국가와 국기 경로 연결 오류: {code}')
            if not re.fullmatch('[0-9a-f]{64}', str(row.get('sha256', ''))):
                raise CatalogError(f'국기 검증 해시 누락: {code}')
            codes.add(code); names.add(name)
        self.countries = data
        self._by_code = {row['code']: row for row in data}

    def get(self, code):
        try:
            return dict(self._by_code[code])
        except KeyError as exc:
            raise CatalogError(f'지원하지 않는 국가 코드: {code}') from exc

    def validate_country(self, code):
        row = self.get(code)
        path = self.root/row['flag']
        try:
            if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
                raise CatalogError(f'국기 파일 해시 불일치: {code}')
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                if min(image.size) < 2:
                    raise CatalogError(f'국기 이미지 크기 오류: {code}')
        except (OSError, SyntaxError) as exc:
            raise CatalogError(f'국기 파일 누락 또는 읽기 실패 ({code}): {exc}') from exc
        row['flag_path'] = str(path.resolve())
        return row

    def valid_countries(self):
        valid, errors = [], []
        for row in self.countries:
            try:
                valid.append(self.validate_country(row['code']))
            except CatalogError as exc:
                errors.append(str(exc))
        return valid, errors
