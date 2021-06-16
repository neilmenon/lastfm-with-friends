import { TestBed } from '@angular/core/testing';

import { BuildService } from './build.service';

describe('BuildService', () => {
  let service: BuildService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(BuildService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
