# iOS accessibility

Каждый значимый control имеет semantic label/traits; decorative content скрыт.
Identifier для automation — отдельная ось. Поддержать Dynamic Type без clipping,
44×44pt hit target, достаточный contrast и информацию не только цветом. Уважать
Reduce Motion/Transparency, когда применимо. Verification включает реальный
VoiceOver order/focus и максимальный размер текста, не только static inspection.

## Семантика и interaction

- Объединять visual fragments в один accessibility element, когда пользователь
  воспринимает их как одну сущность; не дублировать label дочерних элементов.
- Value описывает текущее состояние, hint — результат действия, traits — роль.
- Custom controls должны поддерживать ожидаемые actions, focus и state changes.
- Ошибка, loading и async completion объявляются доступным способом; focus не
  прыгает без причины.
- Text scaling проверяется на реальном layout с длинным локализованным контентом;
  fixed height не обрезает текст.
- Keyboard/Switch Control path проверяется, если surface его поддерживает.

Plan указывает affected semantics и runtime cases. Snapshot не доказывает focus
order, announcement или hit target; для них требуется simulator/device evidence.
