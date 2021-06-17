import { Pipe, PipeTransform } from '@angular/core';
import { formatNumber } from '@angular/common';

@Pipe({
  name: 'pluralize'
})
export class PluralizePipe implements PipeTransform {
  
  transform(number: number, singularText: string, pluralText: string = null): string {
    let pluralWord = pluralText ? pluralText : `${singularText}s`
    let numberFormatted = formatNumber(number, "en-US")
    return number > 1 ? `${numberFormatted} ${pluralWord}` : `${numberFormatted} ${singularText}`
  }

}
